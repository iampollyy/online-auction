"""
Extended business logic tests for Dispute Service.
Tests for dispute validation, status transitions, and event handling.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from main import app
from models import Dispute


# Create test fixtures if they don't exist in conftest
@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def setup_test_db(db_session):
    """Setup test database before each test."""
    # Tables are already created by conftest
    yield db_session


# ==================== DISPUTE CREATION VALIDATION ====================

class TestDisputeCreationValidation:
    """Test business logic for dispute creation."""

    def test_create_dispute_requires_user_id(self, client):
        """user_id is required for dispute creation."""
        payload = {
            "event_type": "BidPlaced",
            "description": "Missing user_id",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 422
        assert "user_id" in resp.text

    def test_create_dispute_requires_event_type(self, client):
        """event_type is required for dispute creation."""
        payload = {
            "user_id": 1,
            "description": "Missing event_type",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 422
        assert "event_type" in resp.text

    def test_create_dispute_with_minimal_fields(self, client):
        """Dispute can be created with only user_id and event_type."""
        payload = {
            "user_id": 1,
            "event_type": "BidPlaced",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["user_id"] == 1
        assert body["event_type"] == "BidPlaced"

    def test_create_dispute_preserves_optional_fields(self, client):
        """Dispute should preserve all optional fields."""
        payload = {
            "artwork_id": 10,
            "bid_id": 20,
            "user_id": 5,
            "event_type": "SuspiciousBidDetected",
            "status": "investigating",
            "is_resolved": False,
            "description": "Suspicious activity detected",
            "resolved_by": None,
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["artwork_id"] == 10
        assert body["bid_id"] == 20
        assert body["user_id"] == 5
        assert body["event_type"] == "SuspiciousBidDetected"
        assert body["status"] == "investigating"
        assert body["is_resolved"] is False
        assert body["description"] == "Suspicious activity detected"
        assert body["resolved_by"] is None

    def test_create_dispute_defaults_status_to_open(self, client):
        """New dispute should default to 'open' status."""
        payload = {
            "user_id": 3,
            "event_type": "AuctionCompleted",
            # status omitted
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["status"] == "open"

    def test_create_dispute_defaults_is_resolved_to_false(self, client):
        """New dispute should default to is_resolved=False."""
        payload = {
            "user_id": 3,
            "event_type": "AuctionCompleted",
            # is_resolved omitted
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["is_resolved"] is False


# ==================== DISPUTE RETRIEVAL ====================

class TestDisputeRetrieval:
    """Test dispute lookup and filtering."""

    def test_get_dispute_by_id(self, client):
        """Should retrieve dispute by ID."""
        # Create first
        create_payload = {
            "user_id": 2,
            "event_type": "BidPlaced",
            "description": "Test lookup",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Retrieve
        resp = client.get(f"/disputes/{dispute_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["dispute_id"] == dispute_id
        assert body["user_id"] == 2
        assert body["event_type"] == "BidPlaced"

    def test_get_nonexistent_dispute_returns_404(self, client):
        """Getting nonexistent dispute should return 404."""
        resp = client.get("/disputes/999999")
        assert resp.status_code == 404
        assert "Dispute not found" in resp.json()["detail"]

    def test_retrieved_dispute_includes_timestamps(self, client):
        """Retrieved dispute should include created_at and updated_at."""
        create_payload = {
            "user_id": 4,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        resp = client.get(f"/disputes/{dispute_id}")
        assert resp.status_code == 200
        body = resp.json()
        # Timestamps may be None in test, but must be in response
        assert "created_at" in body
        assert "updated_at" in body


# ==================== DISPUTE STATUS UPDATES ====================

class TestDisputeStatusUpdates:
    """Test dispute status transitions."""

    def test_update_status_to_investigating(self, client):
        """Should update dispute status from 'open' to 'investigating'."""
        # Create
        create_payload = {
            "user_id": 5,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Update
        update_payload = {"status": "investigating"}
        resp = client.patch(f"/disputes/{dispute_id}/status", json=update_payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "investigating"

    def test_update_status_to_resolved(self, client):
        """Should update dispute status to 'resolved'."""
        create_payload = {
            "user_id": 6,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        update_payload = {
            "status": "resolved",
            "is_resolved": True,
            "resolved_by": "admin@example.com",
        }
        resp = client.patch(f"/disputes/{dispute_id}/status", json=update_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "resolved"
        assert body["is_resolved"] is True
        assert body["resolved_by"] == "admin@example.com"

    def test_partial_status_update(self, client):
        """Should support partial status updates."""
        create_payload = {
            "user_id": 7,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Update only is_resolved
        update_payload = {"is_resolved": True}
        resp = client.patch(f"/disputes/{dispute_id}/status", json=update_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_resolved"] is True
        assert body["status"] == "open"  # Should remain unchanged

    def test_update_resolved_by_field(self, client):
        """Should update the resolved_by field."""
        create_payload = {
            "user_id": 8,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        update_payload = {
            "status": "resolved",
            "resolved_by": "moderator@company.com",
        }
        resp = client.patch(f"/disputes/{dispute_id}/status", json=update_payload)
        assert resp.status_code == 200
        assert resp.json()["resolved_by"] == "moderator@company.com"

    def test_update_nonexistent_dispute_returns_404(self, client):
        """Updating nonexistent dispute should return 404."""
        update_payload = {"status": "resolved"}
        resp = client.patch("/disputes/999999/status", json=update_payload)
        assert resp.status_code == 404


# ==================== STATUS TRANSITION FLOWS ====================

class TestStatusTransitionFlows:
    """Test complete dispute lifecycle flows."""

    def test_flow_open_to_investigating_to_resolved(self, client):
        """Test complete flow: open → investigating → resolved."""
        # Create (open)
        create_payload = {
            "user_id": 10,
            "event_type": "SuspiciousBidDetected",
            "description": "High-value bid flagged",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]
        assert create_resp.json()["status"] == "open"

        # Transition to investigating
        resp1 = client.patch(
            f"/disputes/{dispute_id}/status",
            json={"status": "investigating"}
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "investigating"
        assert resp1.json()["is_resolved"] is False

        # Transition to resolved
        resp2 = client.patch(
            f"/disputes/{dispute_id}/status",
            json={
                "status": "resolved",
                "is_resolved": True,
                "resolved_by": "fraud_team@example.com"
            }
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["status"] == "resolved"
        assert body["is_resolved"] is True
        assert body["resolved_by"] == "fraud_team@example.com"

    def test_flow_with_closed_status(self, client):
        """Test flow ending with 'closed' status."""
        create_payload = {
            "user_id": 11,
            "event_type": "AuctionCompleted",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Go directly to closed
        resp = client.patch(
            f"/disputes/{dispute_id}/status",
            json={"status": "closed"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"


# ==================== DISPUTE BY EVENT TYPE ====================

class TestDisputesByEventType:
    """Test dispute creation for different event types."""

    def test_dispute_for_bidplaced_event(self, client):
        """Should create dispute for BidPlaced event."""
        payload = {
            "user_id": 20,
            "event_type": "BidPlaced",
            "description": "Auto-flagged bid",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["event_type"] == "BidPlaced"

    def test_dispute_for_suspiciousbid_event(self, client):
        """Should create dispute for SuspiciousBidDetected event."""
        payload = {
            "user_id": 21,
            "event_type": "SuspiciousBidDetected",
            "description": "Whale bid detected",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["event_type"] == "SuspiciousBidDetected"

    def test_dispute_for_auctioncompleted_event(self, client):
        """Should create dispute for AuctionCompleted event."""
        payload = {
            "user_id": 22,
            "event_type": "AuctionCompleted",
            "description": "Final bid validation",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["event_type"] == "AuctionCompleted"

    def test_dispute_for_custom_event(self, client):
        """Should accept disputes for custom event types."""
        payload = {
            "user_id": 23,
            "event_type": "CustomEventType",
            "description": "Custom event",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["event_type"] == "CustomEventType"


# ==================== DISPUTE WITH LINKED ENTITIES ====================

class TestDisputesWithLinkedEntities:
    """Test disputes linked to artworks and bids."""

    def test_dispute_linked_to_artwork(self, client):
        """Dispute should properly link to artwork."""
        payload = {
            "artwork_id": 100,
            "user_id": 30,
            "event_type": "BidPlaced",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["artwork_id"] == 100

    def test_dispute_linked_to_bid(self, client):
        """Dispute should properly link to bid."""
        payload = {
            "bid_id": 200,
            "user_id": 31,
            "event_type": "SuspiciousBidDetected",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        assert resp.json()["bid_id"] == 200

    def test_dispute_linked_to_both_artwork_and_bid(self, client):
        """Dispute can link to both artwork and bid."""
        payload = {
            "artwork_id": 100,
            "bid_id": 200,
            "user_id": 32,
            "event_type": "BidPlaced",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["artwork_id"] == 100
        assert body["bid_id"] == 200

    def test_dispute_with_none_linked_entities(self, client):
        """Dispute can be created without artwork/bid links."""
        payload = {
            "user_id": 33,
            "event_type": "AuctionCompleted",
            # artwork_id and bid_id omitted (None)
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["artwork_id"] is None
        assert body["bid_id"] is None


# ==================== DISPUTE PERSISTENCE ====================

class TestDisputePersistence:
    """Test that disputes are properly persisted."""

    def test_created_dispute_retrieved_intact(self, client):
        """Created dispute should be retrievable with all data intact."""
        create_payload = {
            "artwork_id": 301,
            "bid_id": 302,
            "user_id": 40,
            "event_type": "SuspiciousBidDetected",
            "status": "investigating",
            "is_resolved": False,
            "description": "Test persistence",
            "resolved_by": None,
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Retrieve and verify
        get_resp = client.get(f"/disputes/{dispute_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["artwork_id"] == 301
        assert body["bid_id"] == 302
        assert body["user_id"] == 40
        assert body["event_type"] == "SuspiciousBidDetected"
        assert body["status"] == "investigating"
        assert body["is_resolved"] is False
        assert body["description"] == "Test persistence"

    def test_updated_dispute_changes_persisted(self, client):
        """Changes to dispute should be persisted."""
        create_payload = {
            "user_id": 41,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Update
        update_payload = {
            "status": "resolved",
            "is_resolved": True,
            "resolved_by": "admin@test.com"
        }
        update_resp = client.patch(
            f"/disputes/{dispute_id}/status",
            json=update_payload
        )
        assert update_resp.status_code == 200

        # Verify changes persisted
        get_resp = client.get(f"/disputes/{dispute_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["status"] == "resolved"
        assert body["is_resolved"] is True
        assert body["resolved_by"] == "admin@test.com"


# ==================== SCHEMA COMPLIANCE ====================

class TestSchemaCompliance:
    """Test that API responses comply with schema."""

    def test_create_dispute_response_schema(self, client):
        """Create dispute response should match DisputeResponse schema."""
        payload = {
            "user_id": 50,
            "event_type": "BidPlaced",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        
        # Check all required fields present
        required_fields = [
            "dispute_id", "user_id", "event_type", "status",
            "is_resolved", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in body, f"Missing field: {field}"

    def test_get_dispute_response_schema(self, client):
        """Get dispute response should match DisputeResponse schema."""
        # Create
        create_payload = {
            "user_id": 51,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Get
        get_resp = client.get(f"/disputes/{dispute_id}")
        assert get_resp.status_code == 200
        body = get_resp.json()
        
        # Check schema
        required_fields = [
            "dispute_id", "user_id", "event_type", "status",
            "is_resolved", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in body, f"Missing field: {field}"

    def test_patch_dispute_response_schema(self, client):
        """Patch dispute response should match DisputeResponse schema."""
        # Create
        create_payload = {
            "user_id": 52,
            "event_type": "BidPlaced",
        }
        create_resp = client.post("/disputes", json=create_payload)
        dispute_id = create_resp.json()["dispute_id"]

        # Update
        update_payload = {"status": "resolved"}
        patch_resp = client.patch(
            f"/disputes/{dispute_id}/status",
            json=update_payload
        )
        assert patch_resp.status_code == 200
        body = patch_resp.json()
        
        # Check schema
        required_fields = [
            "dispute_id", "user_id", "event_type", "status",
            "is_resolved", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in body, f"Missing field: {field}"
