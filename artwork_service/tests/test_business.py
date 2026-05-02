import pytest
from fastapi import HTTPException

from artwork_service.business import (
    apply_artwork_update,
    apply_price_update,
    apply_status_rules,
    validate_artwork_create,
)
from artwork_service.models import Artwork
from artwork_service.schemas import ArtworkCreate, ArtworkUpdate


def _artwork(**overrides):
    defaults = {
        "title": "Test Art",
        "artist_id": 1,
        "category_id": 1,
        "starting_price": 100.0,
        "current_price": 100.0,
        "status": "available",
        "is_available": True,
    }
    defaults.update(overrides)
    return Artwork(**defaults)


def test_validate_artwork_create_rejects_current_price_below_starting_price():
    data = ArtworkCreate(
        title="Bad Price",
        artist_id=1,
        category_id=1,
        starting_price=100.0,
        current_price=50.0,
    )

    with pytest.raises(HTTPException) as exc:
        validate_artwork_create(data)

    assert exc.value.status_code == 400


def test_apply_status_rules_sold_marks_artwork_unavailable():
    artwork = _artwork()

    apply_status_rules(artwork, "sold")

    assert artwork.status == "sold"
    assert artwork.is_available is False


def test_apply_artwork_update_validates_effective_prices():
    artwork = _artwork(starting_price=100.0, current_price=150.0)

    with pytest.raises(HTTPException) as exc:
        apply_artwork_update(artwork, ArtworkUpdate(starting_price=200.0))

    assert exc.value.status_code == 400


def test_apply_price_update_rejects_sold_artwork():
    artwork = _artwork(status="sold", is_available=False)

    with pytest.raises(HTTPException) as exc:
        apply_price_update(artwork, 200.0)

    assert exc.value.status_code == 400
