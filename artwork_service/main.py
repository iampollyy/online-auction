import logging

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from artwork_service.database import engine, get_db, create_schema, Base
from artwork_service.business import (
    apply_artwork_update,
    apply_price_update,
    apply_status_rules,
    validate_artwork_create,
)
from artwork_service.models import Artwork
from artwork_service.schemas import (
    ArtworkResponse, ArtworkCreate, ArtworkUpdate, PriceUpdate
)
from artwork_service.seed import seed_data

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(title="ArtworkService", version="1.0.0")


@app.on_event("startup")
def startup():
    logger.info("Starting ArtworkService – creating schema, tables, and seeding data")
    create_schema()
    Base.metadata.create_all(bind=engine)
    seed_data()
    logger.info("Startup complete")


# ==================== ARTWORK ENDPOINTS ====================

@app.get("/artworks", response_model=List[ArtworkResponse])
def get_artworks(db: Session = Depends(get_db)):
    logger.info("Fetching all artworks")
    artworks = db.query(Artwork).all()
    logger.info("Returned %d artworks", len(artworks))
    return artworks


@app.get("/artworks/{artwork_id}", response_model=ArtworkResponse)
def get_artwork(artwork_id: int, db: Session = Depends(get_db)):
    logger.info("Fetching artwork id=%d", artwork_id)
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        logger.warning("Artwork id=%d not found", artwork_id)
        raise HTTPException(status_code=404, detail="Artwork not found")
    return artwork


@app.post("/artworks", response_model=ArtworkResponse, status_code=201)
def create_artwork(data: ArtworkCreate, db: Session = Depends(get_db)):
    logger.info("Creating artwork: %s", data.title)
    validate_artwork_create(data)
    artwork = Artwork(**data.model_dump())
    db.add(artwork)
    db.commit()
    db.refresh(artwork)
    logger.info("Created artwork id=%d", artwork.artwork_id)
    return artwork


@app.put("/artworks/{artwork_id}", response_model=ArtworkResponse)
def update_artwork(artwork_id: int, data: ArtworkUpdate, db: Session = Depends(get_db)):
    logger.info("Updating artwork id=%d", artwork_id)
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        logger.warning("Artwork id=%d not found for update", artwork_id)
        raise HTTPException(status_code=404, detail="Artwork not found")
    apply_artwork_update(artwork, data)
    db.commit()
    db.refresh(artwork)
    logger.info("Artwork id=%d updated successfully", artwork_id)
    return artwork


@app.put("/artworks/{artwork_id}/status")
def update_artwork_status(artwork_id: int, status: str, db: Session = Depends(get_db)):
    logger.info("Updating status of artwork id=%d to '%s'", artwork_id, status)
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        logger.warning("Artwork id=%d not found for status update", artwork_id)
        raise HTTPException(status_code=404, detail="Artwork not found")
    apply_status_rules(artwork, status)
    db.commit()
    db.refresh(artwork)
    logger.info("Artwork id=%d status updated to '%s'", artwork_id, status)
    return {"message": f"Artwork {artwork_id} status updated to {status}"}


@app.put("/artworks/{artwork_id}/price", response_model=ArtworkResponse)
def update_artwork_price(artwork_id: int, data: PriceUpdate, db: Session = Depends(get_db)):
    logger.info("Updating price of artwork id=%d to %.2f", artwork_id, data.current_price)
    artwork = db.query(Artwork).filter(Artwork.artwork_id == artwork_id).first()
    if not artwork:
        logger.warning("Artwork id=%d not found for price update", artwork_id)
        raise HTTPException(status_code=404, detail="Artwork not found")
    apply_price_update(artwork, data.current_price)
    db.commit()
    db.refresh(artwork)
    logger.info("Artwork id=%d price updated to %.2f", artwork_id, data.current_price)
    return artwork
