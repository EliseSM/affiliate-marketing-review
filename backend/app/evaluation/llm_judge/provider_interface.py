from abc import ABC, abstractmethod

from app.evaluation.llm_judge.schema import JudgeResult, RubricDimensionInfo


class LLMProvider(ABC):
    """Vendor-agnostic contract for the LLM-as-judge pass. Everything upstream
    (pipeline, API routes) depends only on this interface, never on a specific
    vendor SDK -- see app/evaluation/llm_judge/provider_factory.py for how the
    concrete implementation is selected via config."""

    @abstractmethod
    async def judge(
        self,
        *,
        text: str,
        images: list[bytes],
        rubric_dimensions: list[RubricDimensionInfo],
        prohibited_phrases: list[str],
    ) -> JudgeResult:
        """Score `text` (+ optional `images`) against `rubric_dimensions` and
        extract claims. Implementations should raise on unrecoverable failure
        so the pipeline can mark the evaluation run `failed`."""
        raise NotImplementedError
