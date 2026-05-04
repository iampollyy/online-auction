from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, func
)
from database import Base, SCHEMA


class Dispute(Base):
    __tablename__ = "Dispute"
    __table_args__ = {"schema": SCHEMA}

    dispute_id = Column(Integer, primary_key=True, autoincrement=True)
    artwork_id = Column(Integer, nullable=True)
    bid_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="open")
    is_resolved = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())