from tests.conftest import make_payment, make_student


def test_create_and_get(client):
    s = make_student(client)
    assert s["id"] > 0
    assert s["group"] == "A1"
    assert s["monthly_fee"] == "1000000.00"

    r = client.get(f"/api/students/{s['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Ali Valiyev"


def test_list(client):
    make_student(client, name="A")
    make_student(client, name="B")
    r = client.get("/api/students")
    assert r.status_code == 200
    assert [x["name"] for x in r.json()] == ["A", "B"]


def test_update(client):
    s = make_student(client)
    r = client.patch(f"/api/students/{s['id']}", json={"group": "A2", "monthly_fee": "1500000.00"})
    assert r.status_code == 200
    body = r.json()
    assert body["group"] == "A2"
    assert body["monthly_fee"] == "1500000.00"


def test_delete_empty(client):
    s = make_student(client)
    r = client.delete(f"/api/students/{s['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/students/{s['id']}").status_code == 404


def test_delete_with_payments_blocked(client):
    s = make_student(client)
    make_payment(client, s["id"], "100000.00", "2026-10-05")
    r = client.delete(f"/api/students/{s['id']}")
    assert r.status_code == 409


def test_validation_empty_name(client):
    r = client.post(
        "/api/students",
        json={"name": "   ", "phone": "+998", "group": "A", "monthly_fee": "100.00"},
    )
    assert r.status_code == 422


def test_validation_non_positive_fee(client):
    r = client.post(
        "/api/students",
        json={"name": "A", "phone": "+998", "group": "A", "monthly_fee": "0"},
    )
    assert r.status_code == 422


def test_get_missing(client):
    assert client.get("/api/students/999").status_code == 404
