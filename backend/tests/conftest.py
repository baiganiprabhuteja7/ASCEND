import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import main
from app.database import Base, build_engine, get_db


@pytest.fixture
def test_session_factory(monkeypatch):
    test_engine = build_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    test_session = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        with test_session() as session:
            yield session

    monkeypatch.setattr(main, "create_db_and_tables", lambda: Base.metadata.create_all(bind=test_engine))
    main.app.dependency_overrides[get_db] = override_get_db
    yield test_session
    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def client(test_session_factory):
    with TestClient(main.app) as test_client:
        signup = test_client.post(
            "/auth/signup",
            json={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "TestPassword123!",
                "confirm_password": "TestPassword123!",
            },
        )
        assert signup.status_code == 201
        yield test_client
