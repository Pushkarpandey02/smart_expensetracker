"""Thread-safe in-memory storage for expenses."""

from __future__ import annotations

from decimal import Decimal
from threading import RLock

from src.models import Expense, ExpenseCreate


class ExpenseRepository:
    """Store expenses for the lifetime of the running API process."""

    def __init__(self) -> None:
        self._expenses: dict[int, Expense] = {}
        self._next_id = 1
        self._lock = RLock()

    def create(self, data: ExpenseCreate) -> Expense:
        with self._lock:
            expense = Expense(id=self._next_id, **data.model_dump())
            self._expenses[expense.id] = expense
            self._next_id += 1
            return expense

    def list(self, category: str | None = None) -> list[Expense]:
        with self._lock:
            expenses = list(self._expenses.values())

        if category is None:
            return expenses

        normalized_category = category.casefold()
        return [
            expense
            for expense in expenses
            if expense.category.casefold() == normalized_category
        ]

    def total(self, category: str | None = None) -> Decimal:
        return sum(
            (expense.amount for expense in self.list(category)),
            start=Decimal("0"),
        )

    def delete(self, expense_id: int) -> bool:
        with self._lock:
            return self._expenses.pop(expense_id, None) is not None
