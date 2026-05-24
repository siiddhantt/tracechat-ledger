from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IdResponse(ApiModel):
    id: UUID


class Timestamped(ApiModel):
    created_at: datetime
