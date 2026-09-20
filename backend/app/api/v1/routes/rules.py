from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.db.models.rule_definition import RuleDefinition
from app.schemas.registry import RuleDefinitionOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.get("", response_model=list[RuleDefinitionOut])
async def list_rules(session: DbSession) -> list[RuleDefinitionOut]:
    result = await session.execute(select(RuleDefinition).order_by(RuleDefinition.rule_key))
    return [RuleDefinitionOut.model_validate(rule) for rule in result.scalars().all()]
