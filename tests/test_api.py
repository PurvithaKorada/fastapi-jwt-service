import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


client = TestClient(app)
CREDS = {"email": "a@example.com", "password": "StrongPass123"}


def auth_header(creds=CREDS):
    client.post("/auth/register", json=creds)
    r = client.post("/auth/login", data={"username": creds["email"], "password": creds["password"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_and_duplicate():
    assert client.post("/auth/register", json=CREDS).status_code == 201
    assert client.post("/auth/register", json=CREDS).status_code == 409


def test_validation_errors():
    r = client.post("/auth/register", json={"email": "not-an-email", "password": "short"})
    assert r.status_code == 422


def test_login_wrong_password():
    client.post("/auth/register", json=CREDS)
    r = client.post("/auth/login", data={"username": CREDS["email"], "password": "wrongpass1"})
    assert r.status_code == 401


def test_protected_requires_token():
    assert client.get("/items/").status_code == 401
    assert client.get("/items/", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_item_crud():
    h = auth_header()
    r = client.post("/items/", json={"title": "First", "description": "hello"}, headers=h)
    assert r.status_code == 201
    item_id = r.json()["id"]

    assert client.get(f"/items/{item_id}", headers=h).json()["title"] == "First"
    assert len(client.get("/items/", headers=h).json()) == 1

    r = client.put(f"/items/{item_id}", json={"title": "Updated"}, headers=h)
    assert r.json()["title"] == "Updated"
    assert r.json()["description"] == "hello"

    assert client.delete(f"/items/{item_id}", headers=h).status_code == 204
    assert client.get(f"/items/{item_id}", headers=h).status_code == 404


def test_users_cannot_access_each_others_items():
    h1 = auth_header(CREDS)
    h2 = auth_header({"email": "b@example.com", "password": "StrongPass456"})
    item_id = client.post("/items/", json={"title": "Private"}, headers=h1).json()["id"]
    assert client.get(f"/items/{item_id}", headers=h2).status_code == 404
    assert client.delete(f"/items/{item_id}", headers=h2).status_code == 404
