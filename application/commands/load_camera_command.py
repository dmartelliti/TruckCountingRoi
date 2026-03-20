from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class LoadCameraCommand(BaseModel):
    camera_id: Optional[UUID]