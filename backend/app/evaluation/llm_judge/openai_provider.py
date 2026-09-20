import base64
import logging

from openai import AsyncOpenAI
from pydantic import ValidationError

from app.evaluation.llm_judge.prompt_builder import build_system_prompt, build_user_prompt
from app.evaluation.llm_judge.provider_interface import LLMProvider
from app.evaluation.llm_judge.schema import JudgeResult, RubricDimensionInfo

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """The only module that knows OpenAI SDK specifics. Swapping to another
    vendor means writing a new class implementing LLMProvider -- nothing else
    in the codebase depends on this module directly (see provider_factory.py)."""

    def __init__(self, *, api_key: str, model: str, timeout_seconds: int) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self._model = model

    async def judge(
        self,
        *,
        text: str,
        images: list[bytes],
        rubric_dimensions: list[RubricDimensionInfo],
        prohibited_phrases: list[str],
    ) -> JudgeResult:
        system_prompt = build_system_prompt(rubric_dimensions, prohibited_phrases)
        user_content: list[dict] = [
            {"type": "text", "text": build_user_prompt(text, has_images=bool(images))}
        ]
        for image_bytes in images:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            user_content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        last_error: Exception | None = None
        for attempt in range(2):  # one initial attempt + one retry on schema validation failure
            try:
                if attempt == 1 and last_error is not None:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Your previous response did not match the required schema: "
                                f"{last_error}. Please respond again, strictly matching the schema."
                            ),
                        }
                    )
                completion = await self._client.beta.chat.completions.parse(
                    model=self._model,
                    messages=messages,
                    response_format=JudgeResult,
                )
                parsed = completion.choices[0].message.parsed
                if parsed is None:
                    raise ValueError("Model response could not be parsed against JudgeResult schema.")
                return parsed
            except ValidationError as exc:
                logger.warning("LLM judge response failed schema validation (attempt %s): %s", attempt, exc)
                last_error = exc
                continue

        raise RuntimeError(f"LLM judge failed to produce a schema-valid response: {last_error}")
