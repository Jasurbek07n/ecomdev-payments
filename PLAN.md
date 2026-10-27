# PLAN

Short reference for the architecture choices made before implementation.
Full narrative is in `README.md` and `AI_USAGE.md`.

## Layers

```
HTTP route (app/api/*)   → thin: validate, call service, map errors
Service   (app/services) → business logic + transactions
DB        (app/db)       → SQLAlchemy 2.x models + session
```

## Database

```
students                             payments
  id            INTEGER PK             id            INTEGER PK
  name          TEXT NOT NULL          student_id    INTEGER FK → students.id
  phone         TEXT NOT NULL                          ON DELETE RESTRICT
  group_name    TEXT NOT NULL          amount        NUMERIC(14,2) NOT NULL (>0)
  monthly_fee   NUMERIC(14,2) NOT NULL payment_date  DATE NOT NULL
  created_at    TIMESTAMP              created_at    TIMESTAMP
  updated_at    TIMESTAMP
```

- `group` is a SQL reserved word → column is `group_name`, API field is `group` via alias.
- Money everywhere is `Decimal` / `NUMERIC(14, 2)`; JSON serializes as string.
- SQLite needs `PRAGMA foreign_keys=ON` on every connect for RESTRICT to apply.

## API

| Method | Path                                   |
|--------|----------------------------------------|
| POST   | `/api/students`                        |
| GET    | `/api/students`                        |
| GET    | `/api/students/{id}`                   |
| PATCH  | `/api/students/{id}`                   |
| DELETE | `/api/students/{id}`  → 409 if payments exist |
| POST   | `/api/payments`                        |
| GET    | `/api/students/{id}/payments`          |
| GET    | `/api/debtors?month=YYYY-MM`           |
| GET    | `/debtors?month=YYYY-MM` (spec alias)  |

## Debt algorithm

```
start, next_start = parse_month(YYYY-MM)   # half-open; ValueError → 422

paid_per_student =
  SELECT student_id, COALESCE(SUM(amount), 0)
  FROM payments
  WHERE payment_date >= start AND payment_date < next_start
  GROUP BY student_id

for each student LEFT JOIN paid_per_student:
    paid = coalesced sum (0 if no row)
    if paid < monthly_fee:
        emit { ..., paid, debt: monthly_fee - paid }

sort by debt desc
```

Half-open interval handles month lengths and Dec→Jan correctly.
Overpayers are filtered before subtraction → debt never negative.
Single aggregate query → no N+1.

## Folder structure

```
app/
  main.py
  core/config.py
  db/{database.py, models.py}
  schemas/{student.py, payment.py, debtor.py}
  services/{students.py, payments.py, debtors.py}
  api/{students.py, payments.py, debtors.py}
  static/css/app.css
  static/js/{app.js, students.js}
  templates/{index.html, students.html}
alembic/{env.py, versions/0001_initial.py}
tests/{conftest.py, test_students.py, test_payments.py, test_debtors.py}
README.md  AI_USAGE.md  PLAN.md  pyproject.toml  .gitignore  alembic.ini
```

## Tests (22)

- Students: create / list / get / patch / delete-empty / delete-with-payments→409 /
  missing / empty name / fee ≤ 0.
- Payments: create / list / amount ≤ 0 / unknown student / invalid date.
- Debtors: zero / partial (300k+400k = 700k paid, 300k debt) /
  fully paid excluded / overpaid excluded /
  **cross-month (Sep payment ignored for Oct)** /
  **Dec → Jan boundary** /
  multiple students mixed, sorted / invalid month formats / `/debtors` alias.

## Commit order

1. scaffold + config
2. db models + alembic
3. student CRUD + tests
4. payments + tests
5. debtors + tests
6. web UI
7. README / AI_USAGE / PLAN
