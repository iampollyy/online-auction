from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DisputeBase(BaseModel):
    artwork_id: Optional[int] = None
    bid_id: Optional[int] = None
    user_id: int
    event_type: str
    status: str = "open"
    is_resolved: bool = False
    description: Optional[str] = None
    resolved_by: Optional[str] = None


class DisputeCreate(DisputeBase):
    pass


class DisputeStatusUpdate(BaseModel):
    status: str
    is_resolved: Optional[bool] = None
    resolved_by: Optional[str] = None


class DisputeResponse(DisputeBase):
    dispute_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True