from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
)
from artwork_service.database import Base, SCHEMA


class Artist(Base):
    __tablename__ = "artist"
    __table_args__ = {"schema": SCHEMA}

    artist_id = Column(Integer, primary_key=True, autoincrement=True)
    artist_name = Column(String(100), nullable=False)
    artist_surname = Column(String(100), nullable=False)
    country = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Categories(Base):
    __tablename__ = "categories"
    __table_args__ = {"schema": SCHEMA}

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), nullable=False)


class Artwork(Base):
    __tablename__ = "artwork"
    __table_args__ = {"schema": SCHEMA}

    artwork_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    artist_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.artist.artist_id"),
        nullable=False
    )
    category_id = Column(
        Integer,
        ForeignKey(f"{SCHEMA}.categories.category_id"),
        nullable=False
    )
    starting_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    status = Column(String(50), nullable=False, default="available")
    is_available = Column(Boolean, default=True)
    auction_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())