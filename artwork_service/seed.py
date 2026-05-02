import logging

from artwork_service.database import SessionLocal
from artwork_service.models import Artist, Categories, Artwork

logger = logging.getLogger(__name__)


def seed_data():
    db = SessionLocal()
    try:
        if db.query(Artist).first():
            logger.info("Seed data already exists – skipping")
            return

        
        artists = [
            Artist(artist_name="Pablo", artist_surname="Picasso", country="Spain"),
            Artist(artist_name="Vincent", artist_surname="van Gogh", country="Netherlands"),
            Artist(artist_name="Claude", artist_surname="Monet", country="France"),
            Artist(artist_name="Frida", artist_surname="Kahlo", country="Mexico"),
        ]
        db.add_all(artists)
        db.flush()

        categories = [
            Categories(category_name="Painting"),
            Categories(category_name="Sculpture"),
            Categories(category_name="Photography"),
            Categories(category_name="Digital Art"),
        ]
        db.add_all(categories)
        db.flush()

        artworks = [
            Artwork(
                title="Guernica",
                artist_id=artists[0].artist_id,
                category_id=categories[0].category_id,
                starting_price=1000000.00,
                current_price=1500000.00,
                status="on_auction",
                is_available=True,
                auction_id=1
            ),
            Artwork(
                title="Starry Night",
                artist_id=artists[1].artist_id,
                category_id=categories[0].category_id,
                starting_price=2000000.00,
                current_price=2500000.00,
                status="sold",
                is_available=False,
                auction_id=2
            ),
            Artwork(
                title="Water Lilies",
                artist_id=artists[2].artist_id,
                category_id=categories[0].category_id,
                starting_price=500000.00,
                current_price=500000.00,
                status="available",
                is_available=True,
                auction_id=3
            ),
            Artwork(
                title="The Two Fridas",
                artist_id=artists[3].artist_id,
                category_id=categories[0].category_id,
                starting_price=800000.00,
                current_price=800000.00,
                status="available",
                is_available=True,
                auction_id=None
            ),
            Artwork(
                title="Digital Sunrise",
                artist_id=artists[0].artist_id,
                category_id=categories[3].category_id,
                starting_price=5000.00,
                current_price=7500.00,
                status="on_auction",
                is_available=True,
                auction_id=1
            ),
        ]
        db.add_all(artworks)
        db.commit()
        logger.info("Seed data inserted successfully")
    except Exception as e:
        db.rollback()
        logger.error("Error during seed: %s", e, exc_info=True)
    finally:
        db.close()