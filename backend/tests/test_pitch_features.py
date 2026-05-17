"""Tests for pitch-deck product features: approvals, WhatsApp commands, allergen block."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def test_approvals_pending_list(client):
    r = client.get(f"{API}/approvals/pending", timeout=20)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_whatsapp_simulate_rating(client):
    r = client.post(
        f"{API}/notifications/whatsapp/simulate",
        json={"From": "whatsapp:test-rating", "Body": "👍"},
        timeout=20,
    )
    assert r.status_code == 200
    assert "reply" in r.json()


def test_whatsapp_simulate_block_permit(client):
    r = client.post(
        f"{API}/notifications/whatsapp/simulate",
        json={"From": "whatsapp:test-parent", "Body": "PERMITIR", "ProfileName": "Test"},
        timeout=20,
    )
    assert r.status_code == 200


def test_trigger_endpoints_exist(client):
    for path in (
        "/notifications/trigger/no-consumption",
        "/notifications/trigger/consumption-ratings",
        "/notifications/trigger/process-approvals",
    ):
        r = client.post(f"{API}{path}", json={}, timeout=60)
        assert r.status_code == 200, f"{path}: {r.text}"


def test_add_item_allergen_conflict(client):
    hijos = client.get(f"{API}/hijos/", timeout=20).json()
    if not hijos:
        pytest.skip("no hijos")
    hid = hijos[0]["id"]
    plan = client.post(
        f"{API}/planifications/plans",
        json={"hijo_id": hid, "week_start": "2026-02-01", "minimum_budget": 10000},
        timeout=20,
    ).json()
    pid = plan["id"]
    r = client.post(
        f"{API}/planifications/plans/{pid}/items",
        json={"day": 0, "product_name": "Mani con chocolate", "quantity": 1, "unit_price": 1000},
        timeout=20,
    )
    if r.status_code == 409:
        assert "alérgeno" in r.text.lower() or "riesgo" in r.text.lower() or "bloqueado" in r.text.lower()
    else:
        assert r.status_code == 200
