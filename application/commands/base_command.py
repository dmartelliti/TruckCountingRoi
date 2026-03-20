from pydantic import BaseModel


class BaseCommand(BaseModel):
    type: str
    source: str
