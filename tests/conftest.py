import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def client(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    def _get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_student(client, name="Ali Valiyev", phone="+998901234567", group="A1", fee="1000000.00"):
    r = client.post(
        "/api/students",
        json={"name": name, "phone": phone, "group": group, "monthly_fee": fee},
    )
    assert r.status_code == 201, r.text
    return r.json()


def make_payment(client, student_id, amount, payment_date):
    r = client.post(
        "/api/payments",
        json={"student_id": student_id, "amount": amount, "payment_date": payment_date},
    )
    assert r.status_code == 201, r.text
    return r.json()
