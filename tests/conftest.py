import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure app.db.session uses SQLite during module import in tests.
os.environ["DATABASE_URL"] = "sqlite:///./test_bootstrap.db"


@pytest.fixture()
def client_and_session_factory(monkeypatch):
    import app.main as main_module
    from app.db.base import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(main_module, "init_db", lambda: None)
    monkeypatch.setattr(main_module, "SessionLocal", testing_session_local)

    with TestClient(main_module.app) as client:
        yield client, testing_session_local
