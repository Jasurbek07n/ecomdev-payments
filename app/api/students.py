from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services import students as service

router = APIRouter(prefix="/api/students", tags=["students"])


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    return service.create(db, data)


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return service.list_all(db)


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, student_id)
    except service.StudentNotFound:
        raise HTTPException(status_code=404, detail="Student not found")


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, student_id, data)
    except service.StudentNotFound:
        raise HTTPException(status_code=404, detail="Student not found")


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, student_id)
    except service.StudentNotFound:
        raise HTTPException(status_code=404, detail="Student not found")
    except service.StudentHasPayments:
        raise HTTPException(
            status_code=409,
            detail="Student has payment history and cannot be deleted",
        )
