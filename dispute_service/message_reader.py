import json
import logging
import threading
import time
from azure.servicebus import ServiceBusClient
from dispute_service.config import SERVICE_BUS_LISTEN_CONNECTION_STRING, QUEUE_NAME
from dispute_service.database import SessionLocal
from dispute_service.models import Dispute

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 10


def process_message(message_body: dict):
  
    event_type = message_body.get("eventType", "Unknown")
    logger.info(f"Processing event: {event_type}")

    if event_type == "SuspiciousBidDetected":
        db = SessionLocal()
        try:
            dispute = Dispute(
                artwork_id=message_body.get("artworkId"),
                bid_id=message_body.get("bidId"),
                user_id=message_body.get("userId") or 0,
                event_type=event_type,
                status="open",
                is_resolved=False,
                description=f"Auto-created dispute: suspicious bid detected. "
                            f"Amount: {message_body.get('amount')}",
            )
            db.add(dispute)
            db.commit()
            logger.info(
                f"Dispute created for suspicious bid {message_body.get('bidId')}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create dispute: {e}")
        finally:
            db.close()

    elif event_type == "AuctionCompleted":
        logger.info(
            f"Auction {message_body.get('auctionId')} completed. "
            f"Winner: user {message_body.get('userId')}, "
            f"amount: {message_body.get('amount')}"
        )

    elif event_type == "BidPlaced":
        logger.info(
            f"Bid placed: bid {message_body.get('bidId')}, "
            f"artwork {message_body.get('artworkId')}, "
            f"user {message_body.get('userId')}"
        )

    else:
        logger.warning(f"Unknown event type: {event_type}")


def poll_queue():
    
    logger.info(
        f"Message reader started. Polling every {POLL_INTERVAL_SECONDS}s "
        f"from queue '{QUEUE_NAME}'"
    )

    while True:
        try:
            with ServiceBusClient.from_connection_string(
                SERVICE_BUS_LISTEN_CONNECTION_STRING
            ) as client:
                with client.get_queue_receiver(
                    queue_name=QUEUE_NAME,
                    max_wait_time=5,  
                ) as receiver:
                    messages = receiver.receive_messages(
                        max_message_count=10,
                        max_wait_time=5,
                    )

                    if messages:
                        logger.info(f"Received {len(messages)} message(s)")

                    for msg in messages:
                        try:
                            body = json.loads(str(msg))
                            process_message(body)
                            receiver.complete_message(msg)
                            logger.info(f"Message completed: {body.get('eventType')}")
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON in message: {e}")
                            receiver.complete_message(msg)
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Service Bus connection error: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


def start_message_reader():
    thread = threading.Thread(target=poll_queue, daemon=True)
    thread.start()
    logger.info("Background message reader thread started")
