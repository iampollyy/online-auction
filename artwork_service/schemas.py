from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# --- Artist ---
class ArtistBase(BaseModel):
    artist_name: str
    artist_surname: str
    country: Optional[str] = None


class ArtistCreate(ArtistBase):
    pass


class ArtistResponse(ArtistBase):
    artist_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Category ---
class CategoryBase(BaseModel):
    category_name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    category_id: int

    class Config:
        from_attributes = True


# --- Artwork ---
class ArtworkBase(BaseModel):
    title: str
    artist_id: int
    category_id: int
    starting_price: float
    current_price: float
    status: str = "available"
    is_available: bool = True
    auction_id: Optional[int] = None


class ArtworkCreate(ArtworkBase):
    pass


class ArtworkUpdate(BaseModel):
    title: Optional[str] = None
    starting_price: Optional[float] = None
    current_price: Optional[float] = None
    status: Optional[str] = None
    is_available: Optional[bool] = None
    auction_id: Optional[int] = None


class PriceUpdate(BaseModel):
    current_price: float


class ArtworkResponse(ArtworkBase):
    artwork_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True