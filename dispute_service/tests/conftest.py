"""
Shared test fixtures for the Dispute Service test suite.
Uses an in-memory SQLite database so tests remain fast and isolated.
"""
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from database import Base, get_db

# ── In-memory SQLite engine (StaticPool keeps one connection alive) ──
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_test,
)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    # Override the schema so SQLite won't choke
    from models import Dispute
    Dispute.__table_args__ = {}
    Dispute.__table__.schema = None

    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def db_session(setup_database):
    """Yield a fresh SQLAlchemy session, rolled back after each test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with the DB dependency overridden."""
    from main import app  # import inside fixture to avoid startup side-effects

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()
