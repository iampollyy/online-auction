from fastapi import HTTPException

from artwork_service.models import Artwork
from artwork_service.schemas import ArtworkCreate, ArtworkUpdate


ALLOWED_STATUSES = {"available", "on_auction", "reserved", "sold"}


def validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid artwork status. Allowed values: {', '.join(sorted(ALLOWED_STATUSES))}",
        )


def validate_price(current_price: float, starting_price: float) -> None:
    if current_price < starting_price:
        raise HTTPException(
            status_code=400,
            detail="Current price cannot be lower than starting price",
        )


def apply_status_rules(artwork: Artwork, status: str) -> None:
    validate_status(status)
    artwork.status = status
    if status == "sold":
        artwork.is_available = False
    elif status == "available":
        artwork.is_available = True


def validate_artwork_create(data: ArtworkCreate) -> None:
    validate_status(data.status)
    validate_price(data.current_price, data.starting_price)


def apply_artwork_update(artwork: Artwork, data: ArtworkUpdate) -> None:
    updates = data.model_dump(exclude_unset=True)

    status = updates.get("status")
    if status is not None:
        validate_status(status)

    starting_price = updates.get("starting_price", artwork.starting_price)
    current_price = updates.get("current_price", artwork.current_price)
    validate_price(current_price, starting_price)

    for key, value in updates.items():
        if key != "status":
            setattr(artwork, key, value)

    if status is not None:
        apply_status_rules(artwork, status)


def apply_price_update(artwork: Artwork, current_price: float) -> None:
    if artwork.status == "sold":
        raise HTTPException(status_code=400, detail="Sold artwork price cannot be changed")
    validate_price(current_price, artwork.starting_price)
    artwork.current_price = current_price
