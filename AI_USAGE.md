# AI usage log

Honest, running log of where AI (Claude Code / Claude Opus) was used during
this test, where it helped, and where I had to correct it.

## 2026-10-28 — Planning phase

**Problem.** Turn the Ecomdev brief into a concrete plan before writing any
code: architecture, DB schema, API contract, debt algorithm, test plan.

**AI tool.** Claude Code (Opus 4.7).

**Prompt summary.** I pasted the full test brief and asked the AI to act as a
senior pair programmer: produce a checklist, architecture, schema, API
contract, debt algorithm, folder structure, test plan, build order, and a list
of easy-to-fail traps. Explicitly told it NOT to start coding yet.

**AI output.** A phased plan with:
- A requirement checklist split into REQUIRED / OPTIONAL / NOT NEEDED.
- A 3-layer architecture (route → service → db) and SQLAlchemy schema.
- A debtor algorithm using a half-open month interval `[start, next_start)`
  computed in SQL with a single aggregated subquery.
- A watchlist of 15 common failure modes (float money, Dec→Jan rollover,
  SQLite FK pragma, `group` being a SQL keyword, overpayers appearing as
  debtors with negative debt, etc.).

**My review.** Read it line by line. I agreed with the delete-with-payments →
409 policy (it matches the brief's "preserve accounting integrity"). I
checked that the proposed Pydantic schema actually enforces `monthly_fee > 0`
on the API boundary, not just in the DB. I decided the `group` → `group_name`
column rename was worth the small alias cost in schemas.

**Problem / mistake.** No concrete code mistake at this stage; the plan was
mostly correct. The one thing I corrected: the first draft of the
`StudentCreate` schema used `Field(serialization_alias="group",
validation_alias="group")` on a field literally named `group`, which would
have shadowed Python's built-in and made the service layer awkward. I renamed
the Pydantic field to `group_name` and kept `group` as the API-facing alias.

## 2026-10-28 — Backend scaffolding

**Problem.** Write models, migrations, services, routes, and tests.

**AI tool.** Claude Code (Opus 4.7).

**Prompt summary.** "Implement the plan commit by commit." The AI generated
`app/db/models.py`, `app/services/debtors.py`, Alembic migration, and tests.

**AI output.** Working code on the first pass for most of it. The debtor
service used `coalesce(sum(amount), 0)` in SQL plus a Python-side filter and
sort, which matches the plan.

**My review.** I ran `pytest` after each file and traced the SQL that
SQLAlchemy emitted to make sure the month interval was really half-open and
the subquery was a single aggregated join, not an N+1.

**Problem / mistake.**
1. **`pip install -e .` failed with "Multiple top-level packages discovered".**
   Setuptools saw both `app/` and `alembic/` and refused to guess. The AI's
   initial `pyproject.toml` didn't declare `[tool.setuptools] packages=[...]`.
   I noticed when the install command errored out and fixed the config to list
   `app` and its subpackages explicitly, excluding `alembic`.
2. **`StudentOut` initially tried to populate the `group` field from the ORM
   attribute `group` (which doesn't exist — the attribute is `group_name`).**
   I spotted this while writing the first test and switched to
   `Field(validation_alias="group_name", serialization_alias="group")` with
   `populate_by_name=True`.
3. **SQLite foreign keys.** The AI remembered to add the `PRAGMA
   foreign_keys=ON` event listener, which I would probably have forgotten. I
   verified it by writing `test_delete_with_payments_blocked` and confirming
   it returned 409, not 204.

## 2026-10-28 — Frontend

**Problem.** Build a mobile-friendly debtors page + payment form with no
framework.

**AI tool.** Claude Code (Opus 4.7).

**Prompt summary.** "Produce clean vanilla JS and a mobile-first stylesheet.
No CDN. Internal-tool look, not a landing page."

**AI output.** HTML templates, a stacked-card mobile table style via
`@media (max-width: 640px)`, and a small `api()` helper that unwraps FastAPI's
`detail` validation arrays into human-readable messages.

**My review.** Loaded the page in the browser, resized to a phone width, added
a student, submitted a payment, and watched the debtors table refresh. Checked
that an invalid month (`2026-13`) surfaces a readable error rather than
`[object Object]`.

**Problem / mistake.** The AI's first JS draft inserted student names into the
DOM with `innerHTML = s.name`, which would break on an apostrophe and open an
XSS hole. I added an `escapeHtml` helper and used it everywhere user data is
interpolated.

## What I wrote / decided myself vs. what the AI generated

- **Decided myself:** the delete-with-payments policy, the choice to make
  `/debtors` an alias rather than a separate route, the decision to keep
  `group` as a string column (not a Group table), and the exact phrasing of
  the "what I'd improve" items in the README.
- **AI generated, I reviewed:** most of the Python code, SQL subquery for the
  debtor sum, CSS, and the first drafts of the tests. Every file was read
  before it went into a commit.
- **I corrected:** the setuptools packaging config, the `group` ↔ `group_name`
  Pydantic aliasing, and the XSS hole in the vanilla JS.

## 5–8 sentence summary (for Ecomdev)

I used Claude Code (Opus 4.7) as a pair programmer: it drafted the plan,
scaffolded models and routes, and produced first-pass tests, which I then
reviewed and ran commit by commit. The most useful prompt was the initial one
that asked for a plan with an explicit "easy to accidentally fail" watchlist
before writing any code — it caught the SQLite foreign-key pragma, the `group`
SQL-keyword issue, and the Dec→Jan rollover trap up front. The AI made three
real mistakes I had to catch: a `pyproject.toml` that confused setuptools
between `app/` and `alembic/`, a Pydantic `StudentOut` that tried to read a
non-existent `group` attribute, and vanilla-JS code that used `innerHTML` on
raw student names (a quiet XSS hole). I spotted the packaging error from the
install log, the schema error from the first failing test, and the XSS from
reading the diff before committing. I personally decided the business rules
that aren't code — the delete-with-payments → 409 policy, the `/debtors`
alias, the decision to keep `group` as a string, and the "what I'd improve"
items in the README. Everything in this repo was read before it was committed;
nothing was accepted blindly.
