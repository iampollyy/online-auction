"""Unit tests for artwork_service schemas (pure Pydantic validation)."""
import pytest
from artwork_service.schemas import (
    ArtworkCreate,
    ArtworkUpdate,
    PriceUpdate,
    ArtworkResponse,
)


class TestArtworkCreateSchema:
    def test_valid_artwork(self):
        data = ArtworkCreate(
            title="Test Painting",
            artist_id=1,
            category_id=1,
            starting_price=100.0,
            current_price=150.0,
        )
        assert data.title == "Test Painting"
        assert data.status == "available"
        assert data.is_available is True

    def test_defaults(self):
        data = ArtworkCreate(
            title="X",
            artist_id=1,
            category_id=1,
            starting_price=10.0,
            current_price=10.0,
        )
        assert data.auction_id is None
        assert data.status == "available"

    def test_missing_required_field(self):
        with pytest.raises(Exception):
            ArtworkCreate(artist_id=1, category_id=1, starting_price=10.0, current_price=10.0)


class TestArtworkUpdateSchema:
    def test_partial_update(self):
        data = ArtworkUpdate(title="New Title")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped == {"title": "New Title"}

    def test_empty_update(self):
        data = ArtworkUpdate()
        assert data.model_dump(exclude_unset=True) == {}


class TestPriceUpdateSchema:
    def test_valid_price(self):
        data = PriceUpdate(current_price=999.99)
        assert data.current_price == 999.99

    def test_missing_price(self):
        with pytest.raises(Exception):
            PriceUpdate()


class TestArtworkResponseSchema:
    def test_from_attributes(self):
        data = ArtworkResponse(
            artwork_id=1,
            title="Resp",
            artist_id=1,
            category_id=1,
            starting_price=10.0,
            current_price=10.0,
            status="available",
            is_available=True,
        )
        assert data.artwork_id == 1
        assert data.created_at is None
