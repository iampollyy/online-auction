"""
Shared fixtures for artwork_service tests.
Uses an in-memory SQLite database so no real DB is required.
"""
import sys
import os
from pathlib import Path

# Add parent directory to Python path so artwork_service can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import database as _db_mod
_db_mod.SCHEMA = None

from database import Base
from models import Artist, Categories, Artwork  

for _tbl in Base.metadata.tables.values():
    _tbl.schema = None

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _create_tables(eng):
    """Create tables via raw DDL so we sidestep schema issues entirely."""
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS artist (
                artist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_name VARCHAR(100) NOT NULL,
                artist_surname VARCHAR(100) NOT NULL,
                country VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name VARCHAR(100) NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS artwork (
                artwork_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                artist_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                starting_price REAL NOT NULL,
                current_price REAL NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'available',
                is_available BOOLEAN DEFAULT 1,
                auction_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artist_id) REFERENCES artist(artist_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        """))
        conn.commit()


def _drop_tables(eng):
    with eng.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS artwork"))
        conn.execute(text("DROP TABLE IF EXISTS categories"))
        conn.execute(text("DROP TABLE IF EXISTS artist"))
        conn.commit()


@pytest.fixture(scope="function")
def db_session():
    """Create tables, yield a session, then drop everything."""
    _create_tables(test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        _drop_tables(test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient that uses the test DB session."""
    from artwork_service.database import get_db

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    from artwork_service.main import app

    app.dependency_overrides[get_db] = _override_get_db

    with patch("artwork_service.main.create_schema"), \
         patch("artwork_service.main.Base") as mock_base, \
         patch("artwork_service.main.seed_data"):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()
