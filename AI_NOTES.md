# AI Usage Notes

## Tool used

OpenAI Codex was used as the coding collaborator for this submission.

## AI-generated work versus submitter work

Codex generated both the initial and final drafts of:

- the FastAPI application under `src/`, including request validation, the in-memory repository, and the HTTP routes;
- the pytest suite under `tests/`;
- `requirements.txt`, `pytest.ini`, `.gitignore`, `README.md`, and this
  `AI_NOTES.md` file.

The submitter supplied the complete assignment brief and the time constraint.
Codex recommended and implemented Python with FastAPI, in-memory storage,
server-generated IDs, query-parameter filtering, and OpenAPI/Swagger as the
single optional bonus. No source or test file in this version is represented as
being handwritten by the submitter.

## Validation, testing, and review of the AI output

The generated implementation was reviewed against every required behavior: create, list, category filter, overall total, category total, and delete. The review also checked that the documented commands and response formats match the code.

The test suite was designed to verify:

- successful creation, trimming of text fields, and server-generated IDs;
- monotonic IDs, creation-order listing, and non-reuse of deleted IDs;
- case-insensitive exact category filtering;
- decimal-safe totals, including `0.1 + 0.2`, while keeping amounts as JSON numbers;
- successful deletion with a truly empty `204` response and `404` behavior for unknown IDs;
- rejection of missing fields, blank text, invalid amounts, invalid dates, blank filters, and invalid path IDs;
- isolated in-memory state between tests; and
- availability of `/docs` and `/openapi.json` for the selected bonus.

The exact documented install command, `python -m pip install -r
requirements.txt`, completed successfully. The first generated test run exposed
a Pydantic model-construction error because the `date` field had the same name
as its imported type. The type import was aliased to `Date`. The next run found
that a test annotation used the non-public `pytest.ParameterSet` attribute; the
unnecessary annotation was removed. These fixes were made instead of weakening
or skipping either test.

The final review also found that Pydantic's default OpenAPI schema for a
`Decimal` advertised numeric strings even though the runtime intentionally
rejects them. The validator's JSON-schema input type was set explicitly to a
number, a schema assertion was added to the tests, and the tested Pydantic
version was pinned for reproducibility.

After those changes, `python -m pytest -q` reported `36 passed in 0.53s` from
the repository root. A second run from a freshly copied project tree reported
`36 passed in 0.40s`, confirming that the tests do not rely on unrelated files
in the original workspace.

The exact documented Uvicorn server command was also started from the
repository root and smoke-tested over HTTP. `/openapi.json` returned `200`; an
expense was created with ID `1`; category filtering returned one match; the
category total was `12.5`; deletion returned `204`; and the final list was
empty.

## Decisions made after reviewing AI suggestions

Codex suggested local JSON-file persistence as an alternative to in-memory storage. The submitter chose not to use it because persistence was not required, and process-local storage keeps the implementation and test isolation straightforward. The limitation is documented in `README.md`.

Codex also raised Docker as a possible bonus. It was not used because the instructions allow at most one bonus; OpenAPI/Swagger was selected instead because it directly documents and makes the REST API easier to review without adding a second runtime setup path.

## Important implementation choices checked during review

- Clients submit only `title`, `amount`, `category`, and `date`; the server owns ID assignment.
- Decimal values are used internally to avoid ordinary binary floating-point addition errors, then serialized as JSON numbers to preserve a conventional API contract.
- Category filtering is documented and tested as case-insensitive exact matching rather than substring search.
- Pydantic rejects unknown fields and invalid values instead of silently accepting ambiguous input.
- Tests replace the process-wide repository with a fresh repository for each test, preventing state leakage between cases.
