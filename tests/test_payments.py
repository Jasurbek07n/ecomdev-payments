from tests.conftest import make_payment, make_student


def test_create_and_list(client):
    s = make_student(client)
    make_payment(client, s["id"], "300000.00", "2026-10-05")
    make_payment(client, s["id"], "400000.00", "2026-10-20")

    r = client.get(f"/api/students/{s['id']}/payments")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert {p["amount"] for p in body} == {"300000.00", "400000.00"}


def test_amount_must_be_positive(client):
    s = make_student(client)
    r = client.post(
        "/api/payments",
        json={"student_id": s["id"], "amount": "0", "payment_date": "2026-10-05"},
    )
    assert r.status_code == 422


def test_unknown_student(client):
    r = client.post(
        "/api/payments",
        json={"student_id": 999, "amount": "100.00", "payment_date": "2026-10-05"},
    )
    assert r.status_code == 404


def test_list_for_unknown_student(client):
    assert client.get("/api/students/999/payments").status_code == 404


def test_invalid_date_format(client):
    s = make_student(client)
    r = client.post(
        "/api/payments",
        json={"student_id": s["id"], "amount": "100.00", "payment_date": "not-a-date"},
    )
    assert r.status_code == 422
