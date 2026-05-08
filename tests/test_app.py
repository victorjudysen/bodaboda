import os
import sys
import tempfile
import pytest

# Point DB at a temp file so tests never touch production data
_tmp_db = os.path.join(tempfile.gettempdir(), "test_bodaboda.db")
os.environ["DB_PATH"] = _tmp_db

# Add backend/ to path so we can import app and db directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app as flask_app   # noqa: E402
from db import init_db             # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Re-create an empty schema before every test."""
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)
    init_db()
    yield
    if os.path.exists(_tmp_db):
        os.remove(_tmp_db)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ── Health ────────────────────────────────────────────────────────────────────

def test_health_endpoint_returns_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 999  # intentional failure for CI demo
    assert resp.get_json() == {"status": "ok"}


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_missing_fields_returns_400(client):
    resp = client.post("/api/register", json={"name": "Alice"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_register_invalid_role_returns_400(client):
    resp = client.post("/api/register", json={
        "name": "Alice", "email": "alice@test.com",
        "password": "secret", "role": "admin"
    })
    assert resp.status_code == 400


def test_register_customer_success(client):
    resp = client.post("/api/register", json={
        "name": "Alice Customer",
        "email": "alice@test.com",
        "password": "secret123",
        "role": "customer",
        "phone": "+255700000001",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Alice Customer"
    assert data["role"] == "customer"


def test_register_duplicate_email_returns_409(client):
    payload = {"name": "Bob", "email": "bob@test.com", "password": "pw", "role": "customer"}
    assert client.post("/api/register", json=payload).status_code == 201
    resp = client.post("/api/register", json=payload)
    assert resp.status_code == 409


def test_register_rider_success(client):
    resp = client.post("/api/register", json={
        "name": "Rider Juma",
        "email": "juma@test.com",
        "password": "secret123",
        "role": "rider",
        "bike_plate": "T 999 ZZZ",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["role"] == "rider"
    assert data["rider_id"] is not None


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_missing_fields_returns_400(client):
    resp = client.post("/api/login", json={"email": "x@x.com"})
    assert resp.status_code == 400


def test_login_wrong_credentials_returns_401(client):
    resp = client.post("/api/login", json={
        "email": "nobody@test.com", "password": "wrong"
    })
    assert resp.status_code == 401


def test_login_correct_credentials_returns_user(client):
    client.post("/api/register", json={
        "name": "Carol", "email": "carol@test.com",
        "password": "mypass", "role": "customer"
    })
    resp = client.post("/api/login", json={
        "email": "carol@test.com", "password": "mypass"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Carol"
    assert data["role"] == "customer"


# ── Stats ─────────────────────────────────────────────────────────────────────

def test_stats_endpoint_returns_expected_keys(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "riders" in data
    assert "trips" in data
    assert "customers" in data


def test_stats_reflect_new_registration(client):
    before = client.get("/api/stats").get_json()["customers"]
    client.post("/api/register", json={
        "name": "Dave", "email": "dave@test.com",
        "password": "pw", "role": "customer"
    })
    after = client.get("/api/stats").get_json()["customers"]
    assert after == before + 1
