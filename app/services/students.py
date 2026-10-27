from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Payment, Student
from app.schemas.student import StudentCreate, StudentUpdate


class StudentNotFound(Exception):
    pass


class StudentHasPayments(Exception):
    pass


def create(db: Session, data: StudentCreate) -> Student:
    student = Student(**data.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def list_all(db: Session) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.id)))


def get(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise StudentNotFound
    return student


def update(db: Session, student_id: int, data: StudentUpdate) -> Student:
    student = get(db, student_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


def delete(db: Session, student_id: int) -> None:
    student = get(db, student_id)
    has_payments = db.scalar(select(Payment.id).where(Payment.student_id == student_id).limit(1))
    if has_payments is not None:
        raise StudentHasPayments
    db.delete(student)
    db.commit()
