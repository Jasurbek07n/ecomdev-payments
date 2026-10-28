import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.debtor import DebtorOut
from app.services import debtors as service

router = APIRouter(tags=["debtors"])


def _debtors(db: Session, month: str) -> list[DebtorOut]:
    try:
        return service.list_debtors(db, month)
    except service.InvalidMonth as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/api/debtors", response_model=list[DebtorOut])
def api_debtors(month: str = Query(..., description="YYYY-MM"), db: Session = Depends(get_db)):
    return _debtors(db, month)


# Spec-literal alias: `GET /debtors?month=YYYY-MM`. Shares the same service.
@router.get("/debtors", response_model=list[DebtorOut], include_in_schema=False)
def debtors_alias(month: str = Query(..., description="YYYY-MM"), db: Session = Depends(get_db)):
    return _debtors(db, month)


@router.get("/api/debtors.csv")
def debtors_csv(month: str = Query(..., description="YYYY-MM"), db: Session = Depends(get_db)):
    rows = _debtors(db, month)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["student_id", "name", "phone", "group", "monthly_fee", "paid", "debt"])
    for d in rows:
        writer.writerow([d.student_id, d.name, d.phone, d.group_name,
                         f"{d.monthly_fee:.2f}", f"{d.paid:.2f}", f"{d.debt:.2f}"])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="debtors-{month}.csv"'},
    )
