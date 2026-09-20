from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models.rubric_dimension import RubricDimension
from app.schemas.registry import RubricDimensionOut

router = APIRouter(prefix="/rubric-dimensions", tags=["rubric"])


@router.get("", response_model=list[RubricDimensionOut])
async def list_rubric_dimensions(session: DbSession) -> list[RubricDimensionOut]:
    result = await session.execute(select(RubricDimension).order_by(RubricDimension.sort_order))
    return [RubricDimensionOut.model_validate(dim) for dim in result.scalars().all()]
