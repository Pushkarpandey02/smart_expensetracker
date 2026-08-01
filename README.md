# Smart Expense Tracker API

A small REST API for recording and summarizing personal expenses. It is built with FastAPI and stores data in memory, so no database setup is required.

## Features

- Add an expense with a title, amount, category, and date.
- View all expenses in creation order.
- Filter expenses by category.
- Calculate the overall total or a total for one category.
- Delete an expense by its server-generated ID.
- Explore the API through interactive OpenAPI/Swagger documentation (the optional bonus selected for this submission).

## Requirements

- Python 3.10 or later

## Install dependencies

Run this command from the repository root:

```bash
python -m pip install -r requirements.txt
```

## Start the server

Run this command from the repository root:

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Run the tests

Run this command from the repository root:

```bash
python -m pytest -q
```

## API contract

| Method | Path | Success response | Description |
| --- | --- | --- | --- |
| `POST` | `/expenses` | `201 Created` | Create an expense and return it with a server-generated ID. |
| `GET` | `/expenses` | `200 OK` | Return all expenses in creation order. |
| `GET` | `/expenses?category=Food` | `200 OK` | Return expenses whose category exactly matches the filter, ignoring case and surrounding whitespace. |
| `GET` | `/expenses/total` | `200 OK` | Return the total amount of all expenses. |
| `GET` | `/expenses/total?category=Food` | `200 OK` | Return the total for the matching category. |
| `DELETE` | `/expenses/{expense_id}` | `204 No Content` | Delete an expense. The response body is empty. |

### Create an expense

`POST /expenses` accepts this shape:

```json
{
  "title": "Lunch",
  "amount": 12.5,
  "category": "Food",
  "date": "2026-08-01"
}
```

The `id` is assigned by the server and must not be included in the request. A successful response is:

```json
{
  "id": 1,
  "title": "Lunch",
  "amount": 12.5,
  "category": "Food",
  "date": "2026-08-01"
}
```

IDs are positive, increase monotonically for the lifetime of the process, and are not reused after deletion.

### List and filter expenses

`GET /expenses` returns a JSON array. The optional `category` query parameter performs an exact category match after trimming surrounding whitespace and comparing case-insensitively. For example, `Food`, `FOOD`, and ` food ` match one another, while `Pet Food` does not match `Food`. A category that has no matches returns an empty array.

### Calculate totals

`GET /expenses/total` returns:

```json
{
  "total": 12.5
}
```

Add the optional `category` query parameter to total only matching expenses. An empty collection or a category with no matches returns `{"total": 0}`. Amounts are added using decimal-safe arithmetic and are emitted as JSON numbers, not strings.

### Delete an expense

`DELETE /expenses/{expense_id}` returns `204 No Content` with an empty body when deletion succeeds. An unknown ID returns:

```json
{
  "detail": "Expense not found"
}
```

with status `404 Not Found`.

## Validation

- `title` and `category` are required, trimmed, and cannot be blank.
- `amount` must be a finite JSON number greater than zero. Numeric strings, booleans, zero, and negative values are rejected.
- `date` must be a real calendar date written exactly as `YYYY-MM-DD`.
- Unknown request fields are rejected.
- A supplied `category` query parameter cannot be blank.
- Invalid request bodies, query parameters, and non-integer path IDs return `422 Unprocessable Entity`.

## Storage

Expenses are stored only in the running process's memory. Restarting the server clears all expenses and restarts ID generation at `1`. This behavior is intentional because the assignment allows in-memory storage.

## OpenAPI/Swagger bonus

While the server is running, interactive Swagger documentation is available at `http://localhost:8000/docs`. The OpenAPI schema is available at `http://localhost:8000/openapi.json`.
