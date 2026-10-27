from fastapi import APIRouter, Depends, HTTPException, Query
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
