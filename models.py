"""Request and response models for the expense API."""

from __future__ import annotations

import re
from datetime import date as Date
from decimal import Decimal, InvalidOperation

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _json_number(value: Decimal) -> int | float:
    """Convert a Decimal to a JSON number only at the response boundary."""

    if value == value.to_integral_value():
        return int(value)
    return float(value)


class ExpenseCreate(BaseModel):
    """Fields accepted when a new expense is created."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Short description of the expense")
    amount: Decimal = Field(gt=0, description="Finite monetary amount greater than zero")
    category: str = Field(description="Category used to group and filter expenses")
    date: Date = Field(description="Expense date in YYYY-MM-DD format")

    @field_validator("title", "category", mode="before")
    @classmethod
    def strip_non_empty_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @field_validator("amount", mode="before", json_schema_input_type=float)
    @classmethod
    def require_finite_json_number(cls, value: object) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ValueError("amount must be a JSON number")

        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("amount must be a valid number") from None

        if not amount.is_finite():
            raise ValueError("amount must be finite")
        return amount

    @field_validator("date", mode="before")
    @classmethod
    def require_iso_date(cls, value: object) -> object:
        if isinstance(value, Date):
            return value
        if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
            raise ValueError("date must use YYYY-MM-DD format")
        return value


class Expense(BaseModel):
    """A stored expense, including its server-generated identifier."""

    model_config = ConfigDict(frozen=True)

    id: int = Field(ge=1)
    title: str
    amount: Decimal
    category: str
    date: Date

    @field_serializer("amount", when_used="json")
    def serialize_amount(self, amount: Decimal) -> int | float:
        return _json_number(amount)


class ExpenseTotal(BaseModel):
    """Aggregate expense total."""

    total: Decimal

    @field_serializer("total", when_used="json")
    def serialize_total(self, total: Decimal) -> int | float:
        return _json_number(total)
