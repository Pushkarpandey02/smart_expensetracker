"""FastAPI entry point for the Smart Expense Tracker."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status

from src.models import Expense, ExpenseCreate, ExpenseTotal
from src.repository import ExpenseRepository


app = FastAPI(
    title="Smart Expense Tracker API",
    version="1.0.0",
    description=(
        "A small REST API for creating, listing, filtering, totaling, and "
        "deleting personal expenses. Data is stored in memory."
    ),
)

_repository = ExpenseRepository()


def get_repository() -> ExpenseRepository:
    """FastAPI dependency that makes storage replaceable in tests."""

    return _repository


def get_category_filter(
    category: Annotated[
        str | None,
        Query(description="Case-insensitive exact category filter"),
    ] = None,
) -> str | None:
    if category is None:
        return None

    normalized = category.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="category filter must not be blank",
        )
    return normalized


Repository = Annotated[ExpenseRepository, Depends(get_repository)]
CategoryFilter = Annotated[str | None, Depends(get_category_filter)]


@app.post(
    "/expenses",
    response_model=Expense,
    status_code=status.HTTP_201_CREATED,
    summary="Add an expense",
)
def create_expense(expense: ExpenseCreate, repository: Repository) -> Expense:
    return repository.create(expense)


@app.get(
    "/expenses",
    response_model=list[Expense],
    summary="View or filter expenses",
)
def list_expenses(repository: Repository, category: CategoryFilter) -> list[Expense]:
    return repository.list(category)


@app.get(
    "/expenses/total",
    response_model=ExpenseTotal,
    summary="Calculate total expenses",
)
def calculate_total(repository: Repository, category: CategoryFilter) -> ExpenseTotal:
    return ExpenseTotal(total=repository.total(category))


@app.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense",
)
def delete_expense(expense_id: int, repository: Repository) -> Response:
    if not repository.delete(expense_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
