import logging

from dispute_service.database import SessionLocal
from dispute_service.models import Dispute

logger = logging.getLogger(__name__)


def seed_data():
    db = SessionLocal()
    try:
        if db.query(Dispute).first():
            logger.info("Seed data already exists, skipping.")
            return

        disputes = [
            Dispute(
                artwork_id=1,
                bid_id=1,
                user_id=1,
                event_type="BidPlaced",
                status="open",
                is_resolved=False,
                description="Suspicious bidding pattern detected on artwork #1"
            ),
            Dispute(
                artwork_id=2,
                bid_id=3,
                user_id=3,
                event_type="SuspiciousBidDetected",
                status="investigating",
                is_resolved=False,
                description="Bid amount is unusually high for this category"
            ),
            Dispute(
                artwork_id=2,
                bid_id=4,
                user_id=1,
                event_type="AuctionCompleted",
                status="resolved",
                is_resolved=True,
                description="Dispute about auction completion timing",
                resolved_by="admin@artauction.com"
            ),
            Dispute(
                artwork_id=1,
                bid_id=2,
                user_id=2,
                event_type="BidPlaced",
                status="open",
                is_resolved=False,
                description="User claims bid was placed by mistake"
            ),
        ]
        db.add_all(disputes)
        db.commit()
        logger.info("Seed data inserted successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Seed data insertion failed: {e}")
    finally:
        db.close()