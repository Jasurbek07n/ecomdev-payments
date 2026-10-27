from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services import payments as service
from app.services.students import StudentNotFound

router = APIRouter(tags=["payments"])


@router.post("/api/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, data)
    except StudentNotFound:
        raise HTTPException(status_code=404, detail="Student not found")


@router.get("/api/students/{student_id}/payments", response_model=list[PaymentOut])
def list_payments(student_id: int, db: Session = Depends(get_db)):
    try:
        return service.list_for_student(db, student_id)
    except StudentNotFound:
        raise HTTPException(status_code=404, detail="Student not found")
