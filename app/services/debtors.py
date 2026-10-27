from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Payment, Student
from app.schemas.debtor import DebtorOut


class InvalidMonth(ValueError):
    pass


def parse_month(month: str) -> tuple[date, date]:
    """Return [start_of_month, start_of_next_month) for a 'YYYY-MM' string."""
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise InvalidMonth("month must be in YYYY-MM format")
    try:
        year = int(month[:4])
        mo = int(month[5:])
        start = date(year, mo, 1)
    except ValueError as exc:
        raise InvalidMonth("month must be a valid YYYY-MM value") from exc
    next_start = date(year + 1, 1, 1) if mo == 12 else date(year, mo + 1, 1)
    return start, next_start


def list_debtors(db: Session, month: str) -> list[DebtorOut]:
    start, next_start = parse_month(month)

    # Sum each student's payments inside the requested month in one query.
    paid_subq = (
        select(
            Payment.student_id.label("student_id"),
            func.coalesce(func.sum(Payment.amount), 0).label("paid"),
        )
        .where(Payment.payment_date >= start, Payment.payment_date < next_start)
        .group_by(Payment.student_id)
        .subquery()
    )

    stmt = (
        select(Student, func.coalesce(paid_subq.c.paid, 0))
        .outerjoin(paid_subq, paid_subq.c.student_id == Student.id)
        .order_by(Student.id)
    )

    debtors: list[DebtorOut] = []
    for student, paid_raw in db.execute(stmt).all():
        paid = Decimal(paid_raw or 0)
        if paid >= student.monthly_fee:
            continue
        debt = student.monthly_fee - paid
        debtors.append(
            DebtorOut(
                student_id=student.id,
                name=student.name,
                phone=student.phone,
                group_name=student.group_name,
                monthly_fee=student.monthly_fee,
                paid=paid,
                debt=debt,
            )
        )

    debtors.sort(key=lambda d: d.debt, reverse=True)
    return debtors
