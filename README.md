# To‘lov nazorati — mini payment accounting

Small payment accounting system for an educational center. Tracks students,
monthly payments, and shows who still owes money for a given month.

Built as a hiring test for Ecomdev.

## Features

- Students CRUD (name, phone, group, monthly fee)
- Payments (a student may make multiple partial payments per month)
- Monthly debtors endpoint: who paid less than their monthly fee in month `YYYY-MM`
- Mobile-friendly web UI: debtor list, month selector, payment form, basic students page
- Interactive API docs via FastAPI (`/docs`)

## Technology

- Python 3.12+
- FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic
- SQLite (file-based, zero setup)
- Vanilla HTML + CSS + JavaScript (no build step, no CDN)
- pytest for tests

## Requirements

- Python **3.12** or newer
- `pip` and `venv` (shipped with Python)

## Installation (from zero)

```bash
# 1. Clone
git clone <repo-url> ecomdev-payments
cd ecomdev-payments

# 2. Create and activate a virtualenv
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
# Linux / macOS
source .venv/bin/activate

# 3. Install dependencies
pip install -e ".[dev]"
```

## Database setup

```bash
alembic upgrade head
```

This creates `app.db` (SQLite) in the project root with the `students` and
`payments` tables.

## Run

```bash
uvicorn app.main:app --reload
```

Then open:

- Web UI: http://127.0.0.1:8000/
- Students page: http://127.0.0.1:8000/students-page
- API docs: http://127.0.0.1:8000/docs

## Tests

```bash
pytest
```

22 tests cover student CRUD, payments, and every debtor edge case
(zero / partial / fully-paid / overpaid / cross-month / Dec→Jan / invalid month).

## API endpoints

| Method | Path                                   | Purpose                              |
|--------|----------------------------------------|--------------------------------------|
| POST   | `/api/students`                        | Create a student                     |
| GET    | `/api/students`                        | List all students                    |
| GET    | `/api/students/{id}`                   | Get one student                      |
| PATCH  | `/api/students/{id}`                   | Partial update                       |
| DELETE | `/api/students/{id}`                   | Delete (blocked if payments exist)   |
| POST   | `/api/payments`                        | Add a payment                        |
| GET    | `/api/students/{id}/payments`          | Payments for one student             |
| GET    | `/api/debtors?month=YYYY-MM`           | Debtors for the given month          |
| GET    | `/debtors?month=YYYY-MM`               | Spec-literal alias (same service)    |

## Business logic — how monthly debt is calculated

For a requested month `YYYY-MM`:

1. Parse the month into a half-open interval `[start_of_month, start_of_next_month)`.
2. For every student, sum all payments whose `payment_date` falls inside that
   interval. Students with zero payments count as `paid = 0`.
3. Compute `debt = monthly_fee - paid`.
4. A student is a debtor only when `paid < monthly_fee`. Overpayment never
   produces negative debt — overpayers are simply excluded.
5. The result is sorted by debt, largest first.

The sum is computed in **one** SQL query (left join against an aggregated
subquery), so performance stays flat as the number of students grows.

The half-open interval avoids every month-length and year-boundary bug
(no `BETWEEN` on last day; December correctly rolls into January of the next year).

## Technical decisions

- **SQLite** was chosen because the task is small and the reviewer should be
  able to run it in under a minute. Everything is behind a single `DATABASE_URL`
  setting (`app/core/config.py`), so swapping in PostgreSQL later is a config +
  driver change, not a code change.
- **Decimal money, not float.** Columns are `NUMERIC(14, 2)`, Pydantic schemas
  use `Decimal` with `max_digits=14, decimal_places=2`, and FastAPI serializes
  Decimals as strings in JSON. No binary float ever touches a monetary value.
- **Service layer.** Routes in `app/api/*` are thin: parse → validate → call
  service → map errors to HTTP. Business logic (including the debtor
  calculation) lives in `app/services/*` so it is unit-testable without HTTP.
- **Delete student with payments → 409.** Payment history is accounting data.
  Deleting a student would either silently destroy history (bad) or require a
  cascade (also bad for audit). The DB foreign key uses `ON DELETE RESTRICT`,
  and the API returns 409 Conflict with a clear message. If a student truly
  needs to be removed, delete their payments first — an explicit act, not a
  silent one.
- **Group as a string field.** The spec treats `group` as a label on the
  student, not a managed entity. A `Group` table would add complexity without
  changing any behavior required by the task. Promoting it to its own table is
  a straightforward later migration.
- **SQLite foreign keys.** SQLite ships with FKs **off** by default. An engine
  listener issues `PRAGMA foreign_keys=ON` on every connection, otherwise
  `ON DELETE RESTRICT` would be ignored.
- **Spec-literal `/debtors` alias.** The brief shows the path without the
  `/api` prefix. Both `/api/debtors` and `/debtors` are mounted and call the
  same service — no duplicated logic.

## What I would improve with another week

1. **Authentication and roles.** The current app has no login. In production,
   admins (accountants) and viewers (teachers) would need different access
   levels — probably session-based auth + a role column on an admin user
   table.
2. **PostgreSQL + Docker Compose.** SQLite is fine for the test but not for
   concurrent writes from several accountants. The `DATABASE_URL` abstraction
   is already in place; adding a `docker-compose.yml` with Postgres and a
   migration-on-boot step would make deployment reproducible.
3. **Payment history UI with filtering.** Right now you can see payments per
   student via the API, but the web UI only shows debtors. A dedicated
   payments screen (filter by student, by month, by date range; edit/delete)
   would be the next most-requested feature from an actual accountant.
4. **Audit log.** Who created, edited, or deleted which record and when.
   Append-only `audit_log` table written from a SQLAlchemy event listener.
   Critical as soon as more than one person uses the system.
5. **CSV / Excel export of the debtors list.** Accountants live in
   spreadsheets. A `GET /api/debtors.csv?month=...` endpoint and a download
   button in the UI would be a day of work and a daily time-saver.
