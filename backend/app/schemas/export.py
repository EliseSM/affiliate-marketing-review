import uuid

from pydantic import BaseModel


class ExportRequest(BaseModel):
    submission_ids: list[uuid.UUID]
