from copy import deepcopy
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient


VALID_EXPENSE: dict[str, Any] = {
    "title": "Lunch",
    "amount": 12.50,
    "category": "Food",
    "date": "2026-08-01",
}


def create_expense(
    client: TestClient, **overrides: Any
) -> dict[str, Any]:
    payload = {**VALID_EXPENSE, **overrides}
    response = client.post("/expenses", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def assert_json_number(value: object) -> None:
    """bool is an int subclass, but it is not a valid monetary response."""
    assert isinstance(value, (int, float)) and not isinstance(value, bool)


def test_empty_repository_has_empty_list_and_zero_total(
    client: TestClient,
) -> None:
    expenses_response = client.get("/expenses")
    total_response = client.get("/expenses/total")

    assert expenses_response.status_code == 200
    assert expenses_response.json() == []
    assert total_response.status_code == 200
    assert total_response.json() == {"total": 0}
    assert_json_number(total_response.json()["total"])


def test_create_trims_text_and_returns_complete_expense(
    client: TestClient,
) -> None:
    response = client.post(
        "/expenses",
        json={
            "title": "  Lunch  ",
            "amount": 12.50,
            "category": "  Food  ",
            "date": "2026-08-01",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert set(created) == {"id", "title", "amount", "category", "date"}
    assert created == {
        "id": 1,
        "title": "Lunch",
        "amount": 12.5,
        "category": "Food",
        "date": "2026-08-01",
    }
    assert_json_number(created["amount"])

    list_response = client.get("/expenses")
    assert list_response.status_code == 200
    assert list_response.json() == [created]


def test_ids_are_unique_monotonic_and_results_keep_creation_order(
    client: TestClient,
) -> None:
    first = create_expense(client, title="First")
    second = create_expense(client, title="Second")
    third = create_expense(client, title="Third")

    assert [first["id"], second["id"], third["id"]] == [1, 2, 3]
    assert [item["id"] for item in client.get("/expenses").json()] == [1, 2, 3]


def test_category_filter_is_trimmed_case_insensitive_and_exact(
    client: TestClient,
) -> None:
    food = create_expense(client, title="Lunch", category="Food")
    groceries = create_expense(client, title="Groceries", category="FOOD")
    create_expense(client, title="Train", category="Travel")
    create_expense(client, title="Pet food", category="Pet Food")

    response = client.get("/expenses", params={"category": "  fOoD  "})

    assert response.status_code == 200
    assert response.json() == [food, groceries]
    assert client.get(
        "/expenses", params={"category": "Entertainment"}
    ).json() == []


def test_totals_use_decimal_safe_arithmetic_and_remain_json_numbers(
    client: TestClient,
) -> None:
    create_expense(client, title="Small one", amount=0.1, category="Food")
    create_expense(client, title="Small two", amount=0.2, category="FOOD")
    create_expense(client, title="Ticket", amount=10.25, category="Travel")

    overall_response = client.get("/expenses/total")
    food_response = client.get(
        "/expenses/total", params={"category": " food "}
    )
    missing_response = client.get(
        "/expenses/total", params={"category": "Bills"}
    )

    assert overall_response.status_code == 200
    assert food_response.status_code == 200
    assert missing_response.status_code == 200
    assert overall_response.json() == {"total": 10.55}
    assert Decimal(str(overall_response.json()["total"])) == Decimal("10.55")
    assert Decimal(str(food_response.json()["total"])) == Decimal("0.3")
    assert missing_response.json() == {"total": 0}
    assert_json_number(overall_response.json()["total"])
    assert_json_number(food_response.json()["total"])
    assert_json_number(missing_response.json()["total"])


def test_delete_removes_only_target_and_updates_total(
    client: TestClient,
) -> None:
    deleted = create_expense(client, title="Lunch", amount=12.5)
    retained = create_expense(
        client, title="Train", amount=7.25, category="Travel"
    )

    response = client.delete(f"/expenses/{deleted['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/expenses").json() == [retained]
    assert client.get("/expenses/total").json() == {"total": 7.25}


def test_deleted_ids_are_not_reused(client: TestClient) -> None:
    first = create_expense(client, title="First")
    assert client.delete(f"/expenses/{first['id']}").status_code == 204

    second = create_expense(client, title="Second")

    assert second["id"] == first["id"] + 1


def test_delete_unknown_expense_returns_404_without_changing_state(
    client: TestClient,
) -> None:
    existing = create_expense(client)

    response = client.delete("/expenses/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Expense not found"}
    assert client.get("/expenses").json() == [existing]


def test_delete_with_non_integer_id_is_rejected(client: TestClient) -> None:
    response = client.delete("/expenses/not-an-integer")

    assert response.status_code == 422


INVALID_EXPENSES = [
    pytest.param(
        {key: value for key, value in VALID_EXPENSE.items() if key != field},
        id=f"missing-{field}",
    )
    for field in VALID_EXPENSE
]
INVALID_EXPENSES.extend(
    [
        pytest.param({**VALID_EXPENSE, "title": ""}, id="empty-title"),
        pytest.param(
            {**VALID_EXPENSE, "title": "   "}, id="whitespace-title"
        ),
        pytest.param({**VALID_EXPENSE, "category": ""}, id="empty-category"),
        pytest.param(
            {**VALID_EXPENSE, "category": "   "}, id="whitespace-category"
        ),
        pytest.param({**VALID_EXPENSE, "title": 123}, id="numeric-title"),
        pytest.param(
            {**VALID_EXPENSE, "category": False}, id="boolean-category"
        ),
        pytest.param({**VALID_EXPENSE, "amount": 0}, id="zero-amount"),
        pytest.param({**VALID_EXPENSE, "amount": -1}, id="negative-amount"),
        pytest.param(
            {**VALID_EXPENSE, "amount": "12.5"}, id="numeric-string-amount"
        ),
        pytest.param({**VALID_EXPENSE, "amount": True}, id="boolean-amount"),
        pytest.param(
            {**VALID_EXPENSE, "amount": "not-a-number"},
            id="nonnumeric-amount",
        ),
        pytest.param({**VALID_EXPENSE, "amount": "NaN"}, id="nan-amount"),
        pytest.param(
            {**VALID_EXPENSE, "amount": "Infinity"}, id="infinite-amount"
        ),
        pytest.param(
            {**VALID_EXPENSE, "date": "not-a-date"}, id="malformed-date"
        ),
        pytest.param(
            {**VALID_EXPENSE, "date": "2026-02-30"}, id="impossible-date"
        ),
        pytest.param(
            {**VALID_EXPENSE, "date": "2026-8-1"}, id="noncanonical-date"
        ),
        pytest.param({**VALID_EXPENSE, "id": 99}, id="unknown-id-field"),
    ]
)


@pytest.mark.parametrize("payload", INVALID_EXPENSES)
def test_invalid_expense_is_rejected_without_being_stored(
    client: TestClient, payload: dict[str, Any]
) -> None:
    response = client.post("/expenses", json=deepcopy(payload))

    assert response.status_code == 422
    assert client.get("/expenses").json() == []


@pytest.mark.parametrize("path", ["/expenses", "/expenses/total"])
@pytest.mark.parametrize("category", ["", "   "])
def test_blank_category_query_is_rejected(
    client: TestClient, path: str, category: str
) -> None:
    response = client.get(path, params={"category": category})

    assert response.status_code == 422


def test_malformed_json_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/expenses",
        content=b'{"title": "broken"',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_openapi_and_swagger_document_the_api(client: TestClient) -> None:
    docs_response = client.get("/docs")
    schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert "text/html" in docs_response.headers["content-type"]
    assert schema_response.status_code == 200

    paths = schema_response.json()["paths"]
    assert {"get", "post"}.issubset(paths["/expenses"])
    assert "get" in paths["/expenses/total"]
    assert "delete" in paths["/expenses/{expense_id}"]

    amount_schema = schema_response.json()["components"]["schemas"][
        "ExpenseCreate"
    ]["properties"]["amount"]
    assert amount_schema["type"] == "number"
