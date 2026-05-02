"""Unit tests for the Dispute Service REST API endpoints."""
import pytest


# ────────────────── POST /disputes ──────────────────

class TestCreateDispute:
    def test_create_dispute_returns_201(self, client):
        payload = {
            "user_id": 1,
            "event_type": "BidPlaced",
            "description": "Test dispute",
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["user_id"] == 1
        assert body["event_type"] == "BidPlaced"
        assert body["status"] == "open"
        assert body["is_resolved"] is False
        assert body["dispute_id"] is not None

    def test_create_dispute_with_all_fields(self, client):
        payload = {
            "artwork_id": 10,
            "bid_id": 20,
            "user_id": 5,
            "event_type": "SuspiciousBidDetected",
            "status": "investigating",
            "is_resolved": False,
            "description": "Full-field dispute",
            "resolved_by": None,
        }
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["artwork_id"] == 10
        assert body["bid_id"] == 20

    def test_create_dispute_missing_user_id_returns_422(self, client):
        payload = {"event_type": "BidPlaced"}
        resp = client.post("/disputes", json=payload)
        assert resp.status_code == 422


# ────────────────── GET /disputes/{id} ──────────────────

class TestGetDispute:
    def test_get_existing_dispute(self, client):
        # create first
        payload = {
            "user_id": 2,
            "event_type": "AuctionCompleted",
            "description": "Lookup test",
        }
        create_resp = client.post("/disputes", json=payload)
        dispute_id = create_resp.json()["dispute_id"]

        resp = client.get(f"/disputes/{dispute_id}")
        assert resp.status_code == 200
        assert resp.json()["dispute_id"] == dispute_id
        assert resp.json()["description"] == "Lookup test"

    def test_get_nonexistent_dispute_returns_404(self, client):
        resp = client.get("/disputes/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Dispute not found"


# ────────────── PATCH /disputes/{id}/status ──────────────

class TestUpdateDisputeStatus:
    def test_update_status(self, client):
        # create
        payload = {
            "user_id": 3,
            "event_type": "BidPlaced",
            "description": "Will be resolved",
        }
        create_resp = client.post("/disputes", json=payload)
        dispute_id = create_resp.json()["dispute_id"]

        # update
        update_payload = {
            "status": "resolved",
            "is_resolved": True,
            "resolved_by": "admin@example.com",
        }
        resp = client.patch(
            f"/disputes/{dispute_id}/status", json=update_payload
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "resolved"
        assert body["is_resolved"] is True
        assert body["resolved_by"] == "admin@example.com"

    def test_update_status_partial(self, client):
        payload = {"user_id": 4, "event_type": "BidPlaced"}
        create_resp = client.post("/disputes", json=payload)
        dispute_id = create_resp.json()["dispute_id"]

        resp = client.patch(
            f"/disputes/{dispute_id}/status",
            json={"status": "investigating"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "investigating"
        # is_resolved should remain unchanged
        assert resp.json()["is_resolved"] is False

    def test_update_nonexistent_dispute_returns_404(self, client):
        resp = client.patch(
            "/disputes/99999/status",
            json={"status": "closed"},
        )
        assert resp.status_code == 404


# ────────────── Schema / model sanity checks ──────────────

class TestSchemaValidation:
    def test_dispute_response_contains_timestamps(self, client):
        payload = {"user_id": 7, "event_type": "BidPlaced"}
        create_resp = client.post("/disputes", json=payload)
        body = create_resp.json()
        # SQLite won't auto-generate server_default, so these may be None,
        # but the keys must be present in the response schema.
        assert "created_at" in body
        assert "updated_at" in body

    def test_default_status_is_open(self, client):
        payload = {"user_id": 8, "event_type": "AuctionCompleted"}
        resp = client.post("/disputes", json=payload)
        assert resp.json()["status"] == "open"
