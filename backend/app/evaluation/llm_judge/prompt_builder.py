from app.evaluation.llm_judge.schema import RubricDimensionInfo

SYSTEM_PROMPT_HEADER = """You are a compliance reviewer for affiliate marketing content promoted by a \
consumer financial services company (personal loans, credit cards, and mortgage prequalification). \
Evaluate the submitted content strictly against the rubric below, sourced from the company's affiliate \
marketing compliance guidelines. Score each dimension 0 (Fail), 1 (Partial), or 2 (Pass), and give a \
concise rationale grounded in the actual text/images provided -- do not invent facts about the content. \
Also extract every material factual claim (APR, fee, reward, eligibility, approval odds, savings, or \
other) so it can be checked against evidence. If the content includes images, treat claims or disclosures \
that appear only in an image with the same scrutiny as claims in text."""


def build_system_prompt(
    rubric_dimensions: list[RubricDimensionInfo], prohibited_phrases: list[str]
) -> str:
    rubric_lines = []
    for dim in rubric_dimensions:
        scale = dim.scoring_scale
        rubric_lines.append(
            f"- {dim.display_name} (key: `{dim.key}`): {dim.description}\n"
            f"    0 = {scale.get('0', '')}\n"
            f"    1 = {scale.get('1', '')}\n"
            f"    2 = {scale.get('2', '')}"
        )
    rubric_block = "\n".join(rubric_lines)

    phrase_block = "\n".join(f"- {phrase}" for phrase in prohibited_phrases)

    return (
        f"{SYSTEM_PROMPT_HEADER}\n\n"
        f"## Rubric dimensions (score every one)\n{rubric_block}\n\n"
        f"## Known high-risk phrases (also flag close paraphrases of these, not just exact matches)\n"
        f"{phrase_block}\n"
    )


def build_user_prompt(text: str, has_images: bool) -> str:
    image_note = (
        "\n\nOne or more images accompany this content; evaluate them as part of the same submission."
        if has_images
        else ""
    )
    return f"Evaluate the following affiliate marketing content:\n\n---\n{text}\n---{image_note}"
