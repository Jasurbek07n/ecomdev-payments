from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DebtorOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    student_id: int
    name: str
    phone: str
    group_name: str = Field(serialization_alias="group")
    monthly_fee: Decimal
    paid: Decimal
    debt: Decimal
