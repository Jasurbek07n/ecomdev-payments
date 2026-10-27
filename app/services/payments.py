from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Payment, Student
from app.schemas.payment import PaymentCreate
from app.services.students import StudentNotFound


def create(db: Session, data: PaymentCreate) -> Payment:
    if db.get(Student, data.student_id) is None:
        raise StudentNotFound
    payment = Payment(**data.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def list_for_student(db: Session, student_id: int) -> list[Payment]:
    if db.get(Student, student_id) is None:
        raise StudentNotFound
    return list(
        db.scalars(
            select(Payment)
            .where(Payment.student_id == student_id)
            .order_by(Payment.payment_date.desc(), Payment.id.desc())
        )
    )
