import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    full_name: str | None
    avatar_url: str | None
    created_at: datetime
