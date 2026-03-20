from pydantic import BaseModel
from typing import Dict, Any

class BaseCommand(BaseModel):
    type: str
    payload: Dict[str, Any]
