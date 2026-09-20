import asyncio
import base64
import logging

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)
from pydantic import ValidationError

from app.evaluation.llm_judge.prompt_builder import build_system_prompt, build_user_prompt
from app.evaluation.llm_judge.provider_interface import LLMProvider
from app.evaluation.llm_judge.schema import (
    JudgeResult,
    RubricDimensionInfo,
    validate_dimension_coverage,
)

logger = logging.getLogger(__name__)

# Network/timeout/rate-limit/server errors -- retrying the *same* request
# after a short backoff is the right response, since nothing about the
# request itself was wrong.
_TRANSIENT_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)
_MAX_TRANSIENT_RETRIES = 3

# Malformed/incomplete model output -- retrying makes sense, but backoff
# doesn't; instead we append a corrective instruction and ask again.
_MAX_VALIDATION_RETRIES = 1


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

        validation_attempts = 0
        while True:
            completion = await self._complete_with_transient_retry(messages)

            parsed = completion.choices[0].message.parsed
            try:
                if parsed is None:
                    raise ValueError("Model response could not be parsed against JudgeResult schema.")
                validate_dimension_coverage(parsed, rubric_dimensions)
            except (ValidationError, ValueError) as exc:
                validation_attempts += 1
                logger.warning(
                    "LLM judge response invalid (attempt %s/%s): %s",
                    validation_attempts,
                    _MAX_VALIDATION_RETRIES,
                    exc,
                )
                if validation_attempts > _MAX_VALIDATION_RETRIES:
                    raise RuntimeError(
                        f"LLM judge failed to produce a complete, schema-valid response "
                        f"after {_MAX_VALIDATION_RETRIES} retries: {exc}"
                    ) from exc
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response did not match the required schema, or was "
                            f"missing required fields: {exc}. Please respond again, strictly "
                            "matching the schema and providing a score for every rubric "
                            "dimension listed above."
                        ),
                    }
                )
                continue

            return parsed

    async def _complete_with_transient_retry(self, messages: list[dict]):
        for attempt in range(_MAX_TRANSIENT_RETRIES + 1):
            try:
                return await self._client.beta.chat.completions.parse(
                    model=self._model,
                    messages=messages,
                    response_format=JudgeResult,
                )
            except _TRANSIENT_ERRORS as exc:
                if attempt >= _MAX_TRANSIENT_RETRIES:
                    raise RuntimeError(
                        f"LLM provider call failed after {_MAX_TRANSIENT_RETRIES} retries: {exc}"
                    ) from exc
                delay = 2**attempt  # 1s, 2s, 4s
                logger.warning(
                    "Transient LLM provider error (attempt %s/%s): %s -- retrying in %ss",
                    attempt + 1,
                    _MAX_TRANSIENT_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
