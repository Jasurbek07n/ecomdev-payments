from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _non_empty(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("must not be empty")
    return v


# `group` is a SQL reserved word, so the column is `group_name`. In the API we
# accept and emit the field as `group` (per the spec) via an alias.
class StudentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    phone: str
    group_name: str = Field(validation_alias="group", serialization_alias="group")
    monthly_fee: Decimal = Field(gt=0, max_digits=14, decimal_places=2)

    @field_validator("name", "phone", "group_name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return _non_empty(v)


class StudentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    phone: str | None = None
    group_name: str | None = Field(default=None, validation_alias="group", serialization_alias="group")
    monthly_fee: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)

    @field_validator("name", "phone", "group_name")
    @classmethod
    def _strip(cls, v: str | None) -> str | None:
        return _non_empty(v) if v is not None else v


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    name: str
    phone: str
    group_name: str = Field(serialization_alias="group")
    monthly_fee: Decimal
    created_at: datetime
    updated_at: datetime
