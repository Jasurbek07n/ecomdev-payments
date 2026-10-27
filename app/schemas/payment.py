from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    student_id: int
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    payment_date: date


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    amount: Decimal
    payment_date: date
    created_at: datetime
