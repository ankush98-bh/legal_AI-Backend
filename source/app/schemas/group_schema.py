from pydantic import BaseModel
from datetime import datetime

class GroupBase(BaseModel):
    group_name: str

class GroupCreate(GroupBase):
    pass

class GroupResponse(GroupBase):
    group_id: int
    created_at: datetime

    class Config:
        orm_mode = True