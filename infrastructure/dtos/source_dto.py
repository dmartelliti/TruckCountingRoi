from pydantic import BaseModel
from typing import Optional


class Source(BaseModel):
    clientId: str
    topic: str
    deviceId: Optional[str] = None

