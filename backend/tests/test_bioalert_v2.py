"""BioAlert+ iteration 2 API tests - hijos, meal plans, thumbs voting, read/unread notifications."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

# Use a stable but unique identifier for create+409 duplicate test
TEST_DUP_ID = "0010049901"  # DANIELA AGUILAR ESPINOSA per Biofood seed


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def created_state():
    """Shared mutable state across module tests."""
    return {"hijo_id": None, "plan_id": None, "notification_id": None}


# ---------------- HIJOS ----------------

def test_hijos_list(client):
    r = client.get(f"{API}/hijos/", timeout=30)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_hijos_create_enrichment(client, created_state):
    # Pre-clean: remove any existing hijo with this id to allow create
    existing = client.get(f"{API}/hijos/", timeout=30).json()
    for h in existing:
        if h.get("usuario_identificacion") == TEST_DUP_ID:
            client.delete(f"{API}/hijos/{h['id']}", timeout=15)

    payload = {
        "usuario_identificacion": TEST_DUP_ID,
        "allergens": ["mani"],
        "parent_phone": "whatsapp:+573001112233",
        "notes": "TEST iteration2",
    }
    r = client.post(f"{API}/hijos/", json=payload, timeout=40)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["usuario_identificacion"] == TEST_DUP_ID
    # Should be enriched from Biofood PostgreSQL
    assert data.get("nombre_estudiante"), f"name not enriched: {data}"
    assert "DANIELA" in data["nombre_estudiante"].upper()
    # allergens stored as list
    assert data["allergens"] == ["mani"]
    created_state["hijo_id"] = data["id"]


def test_hijos_create_duplicate_409(client):
    payload = {"usuario_identificacion": TEST_DUP_ID, "allergens": []}
    r = client.post(f"{API}/hijos/", json=payload, timeout=20)
    assert r.status_code == 409, r.text


def test_hijos_get_by_id(client, created_state):
    hid = created_state["hijo_id"]
    if not hid:
        pytest.skip("no hijo created")
    r = client.get(f"{API}/hijos/{hid}", timeout=20)
    assert r.status_code == 200, r.text
    assert r.json()["id"] == hid


def test_hijos_patch(client, created_state):
    hid = created_state["hijo_id"]
    if not hid:
        pytest.skip("no hijo created")
    r = client.patch(f"{API}/hijos/{hid}", json={"notes": "TEST updated", "allergens": ["mani", "lactosa"]}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["notes"] == "TEST updated"
    assert set(data["allergens"]) == {"mani", "lactosa"}


# ---------------- PLANIFICATIONS ----------------

def test_create_meal_plan(client, created_state):
    hid = created_state["hijo_id"]
    if not hid:
        pytest.skip("no hijo created")
    payload = {
        "hijo_id": hid,
        "week_start": "2026-01-05",
        "minimum_budget": 20000.0,
    }
    r = client.post(f"{API}/planifications/plans", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["hijo_id"] == hid
    assert data["minimum_budget"] == 20000.0
    assert data["current_total"] == 0.0
    assert data["goal_met"] is False
    created_state["plan_id"] = data["id"]


def test_add_item_partial(client, created_state):
    pid = created_state["plan_id"]
    if not pid:
        pytest.skip("no plan created")
    r = client.post(
        f"{API}/planifications/plans/{pid}/items",
        json={"day": 0, "product_name": "Yogurt", "quantity": 2, "unit_price": 3500},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["current_total"] == 7000.0
    assert data["goal_met"] is False
    assert (data.get("reward") in (None, "",))


def test_add_item_goal_met(client, created_state):
    pid = created_state["plan_id"]
    if not pid:
        pytest.skip("no plan created")
    extras = [
        {"day": 1, "product_name": "LIMONADA FRAPPE", "quantity": 5, "unit_price": 3000},
        {"day": 2, "product_name": "Galleta", "quantity": 1, "unit_price": 2500},
        {"day": 3, "product_name": "Jugo", "quantity": 1, "unit_price": 2500},
        {"day": 4, "product_name": "Fruta", "quantity": 1, "unit_price": 2500},
    ]
    data = None
    for item in extras:
        r = client.post(f"{API}/planifications/plans/{pid}/items", json=item, timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
    assert data["current_total"] >= 20000.0
    assert data["goal_met"] is True
    assert "10%" in (data.get("reward") or "")


def test_remove_item_recalculates(client, created_state):
    pid = created_state["plan_id"]
    if not pid:
        pytest.skip("no plan created")
    r = client.delete(f"{API}/planifications/plans/{pid}/items/1", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # After removing the big item, total should drop, goal likely no longer met
    assert data["current_total"] == 7000.0
    assert data["goal_met"] is False


def test_active_plan(client, created_state):
    hid = created_state["hijo_id"]
    r = client.get(f"{API}/planifications/hijos/{hid}/active-plan", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data is not None
    assert data["id"] == created_state["plan_id"]


def test_legacy_at_risk_still_works(client):
    r = client.get(f"{API}/planifications/at-risk", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


# ---------------- FEEDBACK ----------------

def test_vote_up(client):
    r = client.post(f"{API}/feedback/vote", json={"product_name": "LIMONADA FRAPPE", "vote": "up"}, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # response should mention vote stored
    assert data.get("vote") == "up" or "id" in data


def test_vote_down(client):
    r = client.post(f"{API}/feedback/vote", json={"product_name": "TEST_DownProduct", "vote": "down"}, timeout=20)
    assert r.status_code == 200, r.text


def test_vote_invalid(client):
    # 'star' is not a valid Literal value -> Pydantic 422 OR 400 if custom validation
    r = client.post(f"{API}/feedback/vote", json={"product_name": "X", "vote": "star"}, timeout=20)
    assert r.status_code in (400, 422), r.text


def test_feedback_products_aggregated(client):
    r = client.get(f"{API}/feedback/products", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    if data:
        sample = data[0]
        for k in ("product_name", "up", "down", "score_pct"):
            assert k in sample, f"missing {k} in {sample}"


def test_feedback_summary(client):
    r = client.get(f"{API}/feedback/summary", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    # At least some of these keys per spec
    keys = set(data.keys())
    assert ("total_votes" in keys) or ("total" in keys)
    assert "up" in keys
    assert "down" in keys


# ---------------- NOTIFICATIONS ----------------

def test_notifications_seed_and_filter(client, created_state):
    # Send a notification to ensure there is at least one unread
    r = client.post(
        f"{API}/notifications/send",
        json={"to": "whatsapp:+573001112233", "body": f"TEST_unread_{uuid.uuid4().hex[:6]}", "kind": "custom"},
        timeout=30,
    )
    # 200 if delivered, 502 if Twilio sandbox rejected, but record should still exist with status='failed'
    assert r.status_code in (200, 502), r.text

    r2 = client.get(f"{API}/notifications/?read=false", timeout=20)
    assert r2.status_code == 200, r2.text
    unread = r2.json()
    assert isinstance(unread, list)
    # find a notif id we can mark read
    if unread:
        created_state["notification_id"] = unread[0].get("id")
        # All returned should be unread
        for n in unread:
            assert n.get("read") in (False, None), f"unexpected read state {n}"


def test_unread_count_endpoint(client):
    r = client.get(f"{API}/notifications/unread-count", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "count" in data
    assert isinstance(data["count"], int)


def test_mark_read_and_unread(client, created_state):
    nid = created_state["notification_id"]
    if not nid:
        pytest.skip("no notification id")
    r = client.post(f"{API}/notifications/{nid}/read", timeout=20)
    assert r.status_code == 200, r.text
    # verify it now appears in read=true
    r2 = client.get(f"{API}/notifications/?read=true&limit=200", timeout=20)
    ids = [n.get("id") for n in r2.json()]
    assert nid in ids
    # Now mark unread
    r3 = client.post(f"{API}/notifications/{nid}/unread", timeout=20)
    assert r3.status_code == 200, r3.text


def test_mark_all_read(client):
    r = client.post(f"{API}/notifications/read-all", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "modified" in data
    # Then unread count should be 0
    r2 = client.get(f"{API}/notifications/unread-count", timeout=20)
    assert r2.json()["count"] == 0


# ---------------- STATISTICS uses thumbs ----------------

def test_statistics_kpis_with_thumbs(client):
    r = client.get(f"{API}/statistics/kpis", timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    # should not crash even with new feedback structure


# ---------------- CLEANUP ----------------

def test_zzz_cleanup_plan_and_hijo(client, created_state):
    pid = created_state.get("plan_id")
    hid = created_state.get("hijo_id")
    if pid:
        client.delete(f"{API}/planifications/plans/{pid}", timeout=20)
    if hid:
        r = client.delete(f"{API}/hijos/{hid}", timeout=20)
        assert r.status_code in (200, 404)
