import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from dispute_service.database import engine, get_db, create_schema, Base
from dispute_service.models import Dispute
from dispute_service.schemas import (
    DisputeResponse, DisputeCreate, DisputeStatusUpdate
)
from dispute_service.seed import seed_data
from dispute_service.message_reader import start_message_reader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    logger.info("Starting DisputeService...")
    create_schema()
    Base.metadata.create_all(bind=engine)
    seed_data()
    start_message_reader()
    logger.info("DisputeService startup complete.")
    yield
    # Optionally add shutdown logic here

app = FastAPI(title="DisputeService", version="1.0.0", lifespan=lifespan)


# ==================== DISPUTE ENDPOINTS ====================

@app.get("/disputes/{dispute_id}", response_model=DisputeResponse)
def get_dispute(dispute_id: int, db: Session = Depends(get_db)):
    logger.info(f"GET /disputes/{dispute_id}")
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        logger.warning(f"Dispute {dispute_id} not found")
        raise HTTPException(status_code=404, detail="Dispute not found")
    logger.info(f"Returning dispute {dispute_id}")
    return dispute


@app.post("/disputes", response_model=DisputeResponse, status_code=201)
def create_dispute(data: DisputeCreate, db: Session = Depends(get_db)):
    logger.info(f"POST /disputes — creating dispute for user {data.user_id}")
    dispute = Dispute(**data.model_dump())
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    logger.info(f"Dispute created with id={dispute.dispute_id}")
    return dispute


@app.patch("/disputes/{dispute_id}/status", response_model=DisputeResponse)
def update_dispute_status(
    dispute_id: int,
    data: DisputeStatusUpdate,
    db: Session = Depends(get_db)
):
    logger.info(f"PATCH /disputes/{dispute_id}/status — new status: {data.status}")
    dispute = db.query(Dispute).filter(Dispute.dispute_id == dispute_id).first()
    if not dispute:
        logger.warning(f"Dispute {dispute_id} not found for status update")
        raise HTTPException(status_code=404, detail="Dispute not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dispute, key, value)
    db.commit()
    db.refresh(dispute)
    logger.info(f"Dispute {dispute_id} status updated to '{dispute.status}'")
    return dispute