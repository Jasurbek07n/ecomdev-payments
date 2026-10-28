from tests.conftest import make_payment, make_student


def _debtors(client, month):
    r = client.get(f"/api/debtors?month={month}")
    assert r.status_code == 200
    return r.json()


def test_zero_payments_full_debt(client):
    s = make_student(client)
    body = _debtors(client, "2026-10")
    assert len(body) == 1
    assert body[0]["paid"] == "0"
    assert body[0]["debt"] == "1000000.00"


def test_partial_payment(client):
    s = make_student(client)
    make_payment(client, s["id"], "300000.00", "2026-10-05")
    make_payment(client, s["id"], "400000.00", "2026-10-20")
    body = _debtors(client, "2026-10")
    assert len(body) == 1
    assert body[0]["paid"] == "700000.00"
    assert body[0]["debt"] == "300000.00"


def test_fully_paid_excluded(client):
    s = make_student(client)
    make_payment(client, s["id"], "1000000.00", "2026-10-05")
    assert _debtors(client, "2026-10") == []


def test_overpaid_excluded(client):
    s = make_student(client)
    make_payment(client, s["id"], "1200000.00", "2026-10-05")
    assert _debtors(client, "2026-10") == []


def test_other_month_not_counted(client):
    """September payment must not reduce October debt."""
    s = make_student(client)
    make_payment(client, s["id"], "800000.00", "2026-09-30")
    make_payment(client, s["id"], "200000.00", "2026-10-05")
    body = _debtors(client, "2026-10")
    assert len(body) == 1
    assert body[0]["paid"] == "200000.00"
    assert body[0]["debt"] == "800000.00"


def test_december_january_boundary(client):
    s = make_student(client)
    make_payment(client, s["id"], "500000.00", "2026-12-31")
    make_payment(client, s["id"], "100000.00", "2027-01-01")

    dec = _debtors(client, "2026-12")
    assert dec[0]["paid"] == "500000.00"
    assert dec[0]["debt"] == "500000.00"

    jan = _debtors(client, "2027-01")
    assert jan[0]["paid"] == "100000.00"
    assert jan[0]["debt"] == "900000.00"


def test_multiple_students_mixed(client):
    a = make_student(client, name="A", fee="1000000.00")
    b = make_student(client, name="B", fee="500000.00")
    c = make_student(client, name="C", fee="2000000.00")
    make_payment(client, a["id"], "1000000.00", "2026-10-05")  # paid off
    make_payment(client, b["id"], "200000.00", "2026-10-05")   # debt 300k
    # c has no payments → debt 2,000,000

    body = _debtors(client, "2026-10")
    names = [d["name"] for d in body]
    # sorted by debt desc: C (2M), B (300k)
    assert names == ["C", "B"]
    assert body[0]["debt"] == "2000000.00"
    assert body[1]["debt"] == "300000.00"


def test_invalid_month_formats(client):
    for bad in ["2026-13", "hello", "2026", "2026-00", "20267-01", "2026-1"]:
        r = client.get(f"/api/debtors?month={bad}")
        assert r.status_code == 422, bad


def test_csv_export(client):
    s = make_student(client)
    make_payment(client, s["id"], "300000.00", "2026-10-05")
    r = client.get("/api/debtors.csv?month=2026-10")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text = r.text.strip().splitlines()
    assert text[0] == "student_id,name,phone,group,monthly_fee,paid,debt"
    assert "700000.00" in text[1]  # debt line


def test_spec_literal_alias_matches(client):
    s = make_student(client)
    make_payment(client, s["id"], "300000.00", "2026-10-05")
    a = client.get("/api/debtors?month=2026-10").json()
    b = client.get("/debtors?month=2026-10").json()
    assert a == b
