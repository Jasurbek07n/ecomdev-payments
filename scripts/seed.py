"""Seed the database with a small demo dataset.

Run after `alembic upgrade head`:

    python -m scripts.seed
"""
from datetime import date
from decimal import Decimal

from app.db.database import SessionLocal
from app.db.models import Payment, Student

STUDENTS = [
    ("Ali Valiyev",   "+998901111111", "English A1",   Decimal("1000000.00")),
    ("Dilnoza Karim", "+998902222222", "English A2",   Decimal("1200000.00")),
    ("Jasur Rahim",   "+998903333333", "IELTS",        Decimal("1500000.00")),
    ("Shahzod Umar",  "+998904444444", "Math 7",       Decimal("800000.00")),
    ("Mohira Sodiq",  "+998905555555", "Robotics",     Decimal("900000.00")),
]

PAYMENTS = [
    # Ali: paid in full for October
    (0, Decimal("1000000.00"), date(2026, 10, 5)),
    # Dilnoza: partial (300k + 400k) → owes 500k in October
    (1, Decimal("300000.00"),  date(2026, 10, 3)),
    (1, Decimal("400000.00"),  date(2026, 10, 20)),
    # Jasur: paid in September but nothing in October → owes full fee in Oct
    (2, Decimal("1500000.00"), date(2026, 9, 28)),
    # Shahzod: overpaid
    (3, Decimal("1000000.00"), date(2026, 10, 10)),
    # Mohira: no payments at all → owes full fee
]


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0:
            print("Database already has students — refusing to re-seed.")
            return

        created: list[Student] = []
        for name, phone, group, fee in STUDENTS:
            s = Student(name=name, phone=phone, group_name=group, monthly_fee=fee)
            db.add(s)
            created.append(s)
        db.flush()

        for idx, amount, pdate in PAYMENTS:
            db.add(Payment(student_id=created[idx].id, amount=amount, payment_date=pdate))

        db.commit()
        print(f"Seeded {len(created)} students and {len(PAYMENTS)} payments.")
        print("Try http://127.0.0.1:8000/?month=2026-10")
    finally:
        db.close()


if __name__ == "__main__":
    main()
