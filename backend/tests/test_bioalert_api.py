"""BioAlert+ end-to-end API tests."""
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


# ---- Health ----
def test_root(client):
    r = client.get(f"{API}/", timeout=20)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


# ---- Statistics ----
def test_statistics_kpis(client):
    r = client.get(f"{API}/statistics/kpis", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    # Expect at least some KPI key
    assert len(data) > 0


def test_statistics_series(client):
    r = client.get(f"{API}/statistics/series", params={"days": 14}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, (list, dict))


def test_statistics_top_products(client):
    r = client.get(f"{API}/statistics/top-products", timeout=30)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), (list, dict))


def test_statistics_activity(client):
    r = client.get(f"{API}/statistics/activity", timeout=30)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), (list, dict))


def test_statistics_schools(client):
    r = client.get(f"{API}/statistics/schools", timeout=30)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), (list, dict))


# ---- Planifications ----
def test_planifications_at_risk(client):
    r = client.get(f"{API}/planifications/at-risk", timeout=40)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, (list, dict))


def test_planifications_balance_specific(client):
    r = client.get(f"{API}/planifications/balance/0010066601", timeout=30)
    # may be 200 or 404 if student not found
    assert r.status_code in (200, 404), r.text


# ---- Discounts ----
_pkg_id = {"id": None}


def test_discounts_generate(client):
    r = client.post(f"{API}/discounts/packages/generate", timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_discounts_list(client):
    r = client.get(f"{API}/discounts/packages", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


def test_discounts_create(client):
    payload = {
        "name": "TEST_Custom Pack",
        "description": "Test package",
        "items": [{"product_name": "Yogurt", "quantity": 2, "unit_price": 3500}],
        "discount_pct": 12,
        "target_segment": "general",
    }
    r = client.post(f"{API}/discounts/packages", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "id" in data
    _pkg_id["id"] = data["id"]


def test_discounts_delete(client):
    pid = _pkg_id["id"]
    if not pid:
        pytest.skip("no package id created")
    r = client.delete(f"{API}/discounts/packages/{pid}", timeout=20)
    assert r.status_code == 200, r.text


# ---- Feedback ----
def test_feedback_create_rating(client):
    payload = {"score": 5, "comment": "TEST_rating great"}
    r = client.post(f"{API}/feedback/ratings", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    assert r.json().get("score") == 5


def test_feedback_list_ratings(client):
    r = client.get(f"{API}/feedback/ratings", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_feedback_summary(client):
    r = client.get(f"{API}/feedback/summary", timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "avg" in data or "average" in data or "count" in data


# ---- Recommendations / Allergens ----
def test_allergens_create(client):
    payload = {
        "usuario_identificacion": "TEST_0010066601",
        "nombre_estudiante": "TEST Student",
        "allergens": ["mani", "lactosa"],
    }
    r = client.post(f"{API}/recommendations/allergens", json=payload, timeout=20)
    assert r.status_code == 200, r.text


def test_allergens_list(client):
    r = client.get(f"{API}/recommendations/allergens", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_allergens_check(client):
    r = client.get(
        f"{API}/recommendations/allergens/check",
        params={"usuario_identificacion": "TEST_0010066601", "product_name": "mani cocido"},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "risk" in data


def test_recommendations_generate(client):
    payload = {"focus": "general"}
    r = client.post(f"{API}/recommendations/generate", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)


def test_recommendations_list(client):
    r = client.get(f"{API}/recommendations/", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


# ---- Notifications / WhatsApp ----
def test_whatsapp_simulate(client):
    payload = {"From": "whatsapp:+573001112233", "Body": "hola, mi saldo?"}
    r = client.post(f"{API}/notifications/whatsapp/simulate", json=payload, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "reply" in data
    assert isinstance(data["reply"], str) and len(data["reply"]) > 0


def test_notifications_list(client):
    r = client.get(f"{API}/notifications/", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_notifications_sessions(client):
    r = client.get(f"{API}/notifications/sessions", timeout=20)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_notifications_send_twilio(client):
    payload = {"to": "whatsapp:+573001112233", "body": "TEST_msg", "kind": "custom"}
    r = client.post(f"{API}/notifications/send", json=payload, timeout=30)
    # Expected: 200 if delivered, or 502 if Twilio sandbox rejects (acceptable per request)
    assert r.status_code in (200, 502), r.text
