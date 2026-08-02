import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SearchCreate(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class SearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    query: str
    created_at: datetime
