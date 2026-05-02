"""Unit tests for the message_reader.process_message function."""
import pytest
from unittest.mock import patch, MagicMock
from message_reader import process_message
from models import Dispute


class TestProcessMessage:
    @patch("message_reader.SessionLocal")
    def test_suspicious_bid_creates_dispute(self, mock_session_cls):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        msg = {
            "eventType": "SuspiciousBidDetected",
            "artworkId": 1,
            "bidId": 42,
            "userId": 7,
            "amount": 999.99,
        }
        process_message(msg)

        mock_db.add.assert_called_once()
        added_obj = mock_db.add.call_args[0][0]
        assert isinstance(added_obj, Dispute)
        assert added_obj.event_type == "SuspiciousBidDetected"
        assert added_obj.bid_id == 42
        assert added_obj.user_id == 7
        assert added_obj.status == "open"
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    @patch("message_reader.SessionLocal")
    def test_suspicious_bid_rollback_on_error(self, mock_session_cls):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db
        mock_db.commit.side_effect = Exception("DB error")

        msg = {
            "eventType": "SuspiciousBidDetected",
            "artworkId": 1,
            "bidId": 42,
            "userId": 7,
            "amount": 100,
        }
        process_message(msg)  # should not raise

        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

    def test_auction_completed_logs_info(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="message_reader"):
            process_message({
                "eventType": "AuctionCompleted",
                "auctionId": 5,
                "userId": 3,
                "amount": 500,
            })
        assert "Auction 5 completed" in caplog.text

    def test_bid_placed_logs_info(self, caplog):
        import logging
        with caplog.at_level(logging.INFO, logger="message_reader"):
            process_message({
                "eventType": "BidPlaced",
                "bidId": 10,
                "artworkId": 2,
                "userId": 4,
            })
        assert "Bid placed" in caplog.text

    def test_unknown_event_logs_warning(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="message_reader"):
            process_message({"eventType": "UnexpectedEvent"})
        assert "Unknown event type" in caplog.text
