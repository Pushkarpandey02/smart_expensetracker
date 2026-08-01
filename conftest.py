from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.main import app, get_repository
from src.repository import ExpenseRepository


@pytest.fixture
def repository() -> ExpenseRepository:
    """Give every test an empty, independent in-memory repository."""
    return ExpenseRepository()


@pytest.fixture
def client(repository: ExpenseRepository) -> Iterator[TestClient]:
    """Exercise the API while replacing its process-wide repository."""

    def override_repository() -> ExpenseRepository:
        return repository

    app.dependency_overrides[get_repository] = override_repository
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
