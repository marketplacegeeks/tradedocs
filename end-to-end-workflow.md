# End-to-End Development Workflow — TradeDocs
### A PM's Guide to Building with Claude Code

**Project:** TradeDocs — trade document platform for export trading houses
**Stack:** Django 5.x + DRF (backend) · React 18 + TypeScript + Ant Design (frontend) · PostgreSQL (Railway)
**Key reference files:** `requirements.md` (PRD v1.2) · `technical_architecture.md` (authoritative constraints)
**Who this is for:** A product manager using Claude Code for the first time, learning AI-assisted development.

---

## How to Read This Document

This workflow has five stages:

- **Stage 1 — Machine Setup:** Done once.
- **Stage 2 — Project Bootstrap:** Done once. Sets up the TradeDocs repository structure.
- **Stage 3 — Claude Code Power Setup:** Done once. **This is new and critical.** Sets up CLAUDE.md, MCP servers, and skills so every session starts smart.
- **Stage 4 — Development Loop:** Done every working session, repeatedly.
- **Stage 5 — Feature Build Order:** The backlog. Which features to build and in what order.

Do not skip stages. Each one creates the foundation the next relies on.

---

## What Is Claude Code? (Read This First)

Claude Code is an AI agent that lives in your terminal and works directly with your project files. It can read, write, and edit code; run commands; search your codebase; and call external tools (MCP servers).

The key mental model: **Claude Code is a junior developer who never forgets your project rules — as long as you write those rules down.** The way you write rules down is through files called `CLAUDE.md`.

There are three kinds of things that make Claude Code smarter:

| Thing | What it is | Where it lives |
| --- | --- | --- |
| **CLAUDE.md** | A markdown file Claude reads automatically before every response. Put your project rules, constraints, and context here. | Project root (and `~/.claude/CLAUDE.md` for global rules) |
| **MCP Servers** | External tools Claude can call — like a live database connection, or browser automation. They extend what Claude can do beyond file editing. | Configured in `~/.claude/settings.json` |
| **Skills (Slash Commands)** | Reusable prompt templates you invoke with `/skill-name`. Like a macro for your most common Claude Code requests. | `~/.claude/commands/` directory |

---

---

# STAGE 1: Machine Setup
## Done once.

---

## Step 1 — Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew --version
```

---

## Step 2 — Install Git

```bash
brew install git
git config --global user.name "Your Name"usergit config --global user.email "your@email.com"
git config --global init.defaultBranch main
```

---

## Step 3 — Create a GitHub Account and Connect Your Mac

1. Create a free account at github.com.
2. Generate an SSH key:

```bash
ssh-keygen -t ed25519 -C "your@email.com"
pbcopy < ~/.ssh/id_ed25519.pub
```

3. Go to GitHub → Settings → SSH and GPG Keys → New SSH Key. Paste and save.
4. Test: `ssh -T ````git@github.com` — you should see `Hi [username]! You've successfully authenticated.`

---

## Step 4 — Install OrbStack (Docker Manager)

OrbStack runs PostgreSQL locally in a Docker container — the same database TradeDocs uses in production.

```bash
brew install --cask orbstack
```

Open OrbStack from Applications and let it finish first-time setup.

```bash
docker --version
docker compose version
```

---

## Step 5 — Install Python 3.12

```bash
brew install pyenv
pyenv install 3.12.0
pyenv global 3.12.0
```

Add `pyenv` to your shell profile:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
python --version   # must say Python 3.12.x
```

---

## Step 6 — Install Node.js

```bash
brew install node
node --version    # v20+ recommended
npm --version
```

---

## Step 7 — Install Claude Code

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

---

## Machine Setup Checklist

```bash
brew --version
git --version
docker --version
docker compose version
python --version   # 3.12.x
node --version     # v20+
npm --version
claude --version
```

If any fail, fix that step before moving on.

---

---

# STAGE 2: Project Bootstrap
## Done once.

---

## Step 8 — Create the GitHub Repository

1. Go to github.com → New repository.
2. Name it `tradetocs`. Set it to Private. Do not initialise with a README (you'll push your own files).
3. Copy the SSH clone URL.

---

## Step 9 — Create the Project Structure Locally

```bash
mkdir ~/Documents/Development/TradeDocs
cd ~/Documents/Development/TradeDocs
git init
git remote add origin git@github.com:yourusername/tradetocs.git
```

---

## Step 10 — Create the Backend Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

Add `.venv/` to `.gitignore`.

Every terminal session that runs Django commands must activate the venv first:

```bash
source .venv/bin/activate
```

---

## Step 11 — Install Backend Dependencies

```bash
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers django-filter psycopg2-binary reportlab pillow gunicorn python-decouple pytest-django factory-boy pytest-cov freezegun
pip freeze > requirements.txt
```

`pytest-cov` generates test coverage reports. `freezegun` lets you freeze or mock the current datetime in tests — useful for document number generation and timestamp fields.

---

## Step 12 — Scaffold Django Project

```bash
source .venv/bin/activate
django-admin startproject tradetocs .
mkdir apps
```

---

## Step 12b — Configure pytest

Create `pytest.ini` in the project root:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = tradetocs.settings
python_files = tests/*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

Verify pytest finds your project (it will find 0 tests for now — that is correct):

```bash
source .venv/bin/activate
pytest --collect-only
```

You should see `no tests ran`. That confirms pytest is wired to Django correctly. As you build each app, its tests will appear here automatically.

**How tests are organised:** Each app gets its own `tests/` directory. When you build `apps/accounts/`, you will also create:

```
apps/accounts/tests/__init__.py
apps/accounts/tests/factories.py   ← factory-boy factories for creating test data
apps/accounts/tests/test_models.py ← model validation tests
apps/accounts/tests/test_views.py  ← API endpoint tests
```

Claude will create these files as part of each feature, alongside the feature code.

---

## Step 13 — Install Frontend Dependencies

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom @tanstack/react-query axios react-hook-form zod antd dayjs
cd ..
```

---

## Step 14 — Start Local Infrastructure (PostgreSQL)

Create `docker-compose.yml` in the project root:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: tradetocs
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Start it:

```bash
docker compose up -d
docker compose ps   # should show db running
```

---

## Step 15 — Configure Environment Variables

```bash
cp .env.example .env
```

Contents of `.env`:

```
TRADETOCS_SECRET_KEY=<generate a random 50-char string>
TRADETOCS_DEBUG=True
TRADETOCS_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://postgres:postgres@localhost:5432/tradetocs

TRADETOCS_EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
TRADETOCS_DEFAULT_FROM_EMAIL=dev@tradetocs.local

TRADETOCS_ACCESS_TOKEN_LIFETIME_MINUTES=30
TRADETOCS_REFRESH_TOKEN_LIFETIME_DAYS=7

VITE_API_BASE_URL=http://localhost:8000
```

Verify `.env` is gitignored:

```bash
git check-ignore -v .env
```

If it prints nothing, add `.env` to `.gitignore` now.

---

## Step 16 — Run Migrations and Create a Superuser

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py createsuperuser
```

The superuser is your initial Company Admin account.

---

## Step 17 — Verify Both Servers Start

**Backend:**

```bash
source .venv/bin/activate
python manage.py runserver
```

Visit `http://localhost:8000/api/v1/auth/me/` — you should see a 401 (unauthenticated). That means the API is running.

**Frontend:**

```bash
cd frontend && npm run dev
```

Visit `http://localhost:5173` — you should see the Vite + React starter page.

---

## Step 18 — Make the Bootstrap Commit

```bash
git add .
git commit -m "Bootstrap: project structure, venv, docker-compose, initial migrations"
git push -u origin main
```

---

---

# STAGE 3: Claude Code Power Setup
## Done once. Makes every future session significantly better.

This stage is the one most beginners skip — and it's why their Claude Code experience feels inconsistent. Do this before writing a single line of feature code.

---

## Step 19 — Create a Global CLAUDE.md (Your Personal Rules)

This file is read by Claude Code in every project on your machine. Put rules that apply universally to how you work.

```bash
mkdir -p ~/.claude
```

Create `~/.claude/CLAUDE.md`:

```markdown
# My Global Rules for Claude Code

## How I Work
- I am a product manager learning to build with AI. Explain technical decisions briefly so I understand them.
- I prefer simple solutions over clever ones. If there are two ways to do something, always show me the simpler one first.
- Never assume I know what an error means. When something fails, tell me what went wrong in plain English before showing me the fix.

## Code Style Preferences
- Always add a brief comment above functions that do something non-obvious.
- Use clear variable names over short ones.

## What to Always Do
- Before writing any code, confirm which files you will touch and why.
- After writing code, tell me what to run to verify it works.
- When I ask you to fix something, touch only the specific thing that is broken. Do not "clean up" surrounding code.

## What to Never Do
- Never start implementing until I say "go ahead" or similar confirmation.
- Never rename things just because you think a name is better.
- Never add features I did not ask for.
```

---

## Step 20 — Create a Project CLAUDE.md (TradeDocs-Specific Rules)

This file lives in the project root. Claude Code reads it automatically whenever you run `claude` inside this project.

Create `/Users/aniket/Documents/Development/TradeDocs/CLAUDE.md`:

```markdown
# TradeDocs — Project Rules for Claude Code

## What This Project Is
Single-tenant trade document platform for an export trading house.
Three document types: Proforma Invoice → Packing List → Commercial Invoice.
Maker creates, Checker approves, Company Admin manages everything.

## Authoritative Documents (Read Before Any Task)
- `requirements.md` — PRD v1.2. All functional requirements, user stories, validation rules.
- `technical_architecture.md` — Tech stack, DB schema, API structure, 30 hard constraints. **Section 9 is law.**

## Non-Negotiable Technical Rules
These come from technical_architecture.md Section 9. Never violate them:

1. All monetary amounts: `DecimalField(max_digits=15, decimal_places=2)`. Never FloatField.
2. All weights: `DecimalField(max_digits=12, decimal_places=3)`. Never FloatField.
3. All FK references to master data: `on_delete=PROTECT`.
4. Organisation records are never hard-deleted — set `is_active=False`.
5. ALL document status transitions go through `WorkflowService` in `apps/workflow/services.py`. Never update `status` anywhere else.
6. `WorkflowService` must write an `AuditLog` entry in the same `transaction.atomic()` as the status update.
7. REJECT, REWORK, PERMANENTLY_REJECT, and DISABLE actions must block if comment is empty.
8. Document numbers (PI/PL/CI) are generated with `select_for_update()` to prevent duplicates.
9. PDF generation always happens in memory and is streamed. Never write a PDF to disk.
10. Every DRF view must explicitly declare `permission_classes`.
11. All Axios calls live in `src/api/*.ts`. No component calls Axios directly.
12. Status strings in the frontend come from `src/utils/constants.ts`. Never hardcode "DRAFT", "APPROVED", etc.

## Folder Structure (Quick Reference)
Backend apps live under `apps/`:
- `apps/accounts/` — Users, roles, JWT auth
- `apps/master_data/` — Organisations, Banks, Countries, Ports, etc.
- `apps/proforma_invoice/` — PI model, line items, charges
- `apps/packing_list/` — PL, containers, container items
- `apps/commercial_invoice/` — CI, aggregated line items
- `apps/workflow/` — WorkflowService, AuditLog
- `pdf/` — ReportLab PDF generation utilities

Frontend pages live under `frontend/src/pages/`.

## Document Number Formats
- Proforma Invoice: `PI-YYYY-NNNN`
- Packing List: `PL-YYYY-NNNN`
- Commercial Invoice: `CI-YYYY-NNNN`

## Testing Rules
- Every app has a `tests/` directory with `__init__.py`, `factories.py`, `test_models.py`, and `test_views.py`.
- Every model must have a factory in `tests/factories.py` using factory-boy.
- Every API endpoint must have at minimum: one happy-path test and one permission-denial test.
- Run tests with `pytest`, never `python manage.py test`.
- All tests must pass before any `git commit`. Run `pytest` and confirm 0 failures before committing.
- Use `pytest --cov=apps/{app} --cov-report=term-missing` to check coverage after completing a feature.
- Factories must use `SubFactory` for related models — never hardcode IDs in tests.

## Current Status
Project is bootstrapped. No feature code written yet.
```

---

## Step 21 — Install MCP Servers

MCP (Model Context Protocol) servers are external tools that Claude Code can call. Think of them as giving Claude a set of hands to reach into systems it normally can not access.

For TradeDocs, two MCP servers are genuinely useful:

### MCP Server 1: PostgreSQL (inspect and query your live database)

This lets Claude Code look directly at your database tables, schema, and data during development. Instead of guessing what is in the database, Claude can ask it directly.

```bash
npm install -g @modelcontextprotocol/server-postgres
```

### MCP Server 2: Filesystem (enhanced file operations)

Claude Code already has file access, but this MCP gives it richer directory browsing capabilities.

```bash
npm install -g @modelcontextprotocol/server-filesystem
```

### Configure MCP Servers

Create or edit `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:postgres@localhost:5432/tradetocs"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/aniket/Documents/Development/TradeDocs"
      ]
    }
  }
}
```

**Verify MCP is connected:** Start Claude Code and type `/mcp` — it should list your connected servers.

### When to Use the PostgreSQL MCP

Use it when you want Claude to:
- Verify a migration actually created the correct columns: *"Check the database and confirm the Organisation table has all the fields defined in the model."*
- Debug a query: *"Run this query against the database and show me what it returns."*
- Confirm seed data loaded: *"Query the Country table and show me the first 5 rows."*

---

## Step 22 — Create Custom Skills (Slash Commands)

Skills are reusable prompt templates that you invoke with a `/command`. They save you from typing the same context-setting paragraph at the start of every session.

Create the skills directory:

```bash
mkdir -p ~/.claude/commands
```

### Skill 1: `/session-start`

This replaces the lengthy session-start prompt from the old workflow. Run it at the beginning of every working session.

Create `~/.claude/commands/session-start.md`:

```markdown
Session start for TradeDocs.

Read in this order:
1. `technical_architecture.md` — focus on Section 9 (constraints). These are non-negotiable.
2. `memory/MEMORY.md` — what was completed last session, what failed, what is next.
3. The relevant section of `requirements.md` for today's task (ask me which one if unclear).

Then report back:
- What the active task is (from MEMORY.md)
- Which files you will touch (using the folder structure in technical_architecture.md Section 3 and 6)
- Which constraints from Section 9 apply to this task
- Any unresolved failures from MEMORY.md

Do not write any code until I confirm your understanding is correct.
```

### Skill 2: `/session-end`

Run this at the end of every session to update memory.

Create `~/.claude/commands/session-end.md`:

```markdown
Session end for TradeDocs.

Update `memory/MEMORY.md` with:
1. What was completed today — be specific, include file names and FR numbers
2. What failed and why — even if fixed, log the error and root cause
3. Any new pattern or constraint discovered that should be noted
4. The exact next action for next session — one sentence, imperative form, e.g. "Write the serializer for OrganisationAddress."

Do not invent progress. Only log what actually passed and is verifiable.
```

### Skill 3: `/feature-plan`

Use this before starting any new feature to get a safe, scoped implementation plan.

Create `~/.claude/commands/feature-plan.md`:

```markdown
I want to implement a new feature. Before writing any code:

1. Read the relevant FR section from `requirements.md` that I will specify.
2. List every file you will create or modify, with one sentence explaining why.
3. List every constraint from `technical_architecture.md` Section 9 that applies.
4. Identify any dependencies — master data, other models, or services that must exist first.
5. Break the implementation into steps: Model → Serializer → View → URL → Frontend API call → Page component.
6. Flag any ambiguity in the requirements before starting.

Then wait for my confirmation before writing anything.
```

### Skill 4: `/verify`

Use this after writing any backend feature to confirm it actually works. It covers both automated tests and manual checks.

Create `~/.claude/commands/verify.md`:

```markdown
I just implemented a feature. Help me verify it works.

Step 1 — Automated tests:
1. Run `pytest apps/{app}/tests/ -v` and show me the output. If any tests fail, diagnose the root cause before suggesting a fix.
2. Run `pytest apps/{app}/tests/ --cov=apps/{app} --cov-report=term-missing` and identify any untested critical paths.

Step 2 — Manual spot-check:
3. Tell me what `curl` commands or browser URLs I should hit to confirm each endpoint works end-to-end.
4. Tell me what database query I can run (via the postgres MCP) to confirm data was saved correctly.
5. Tell me what visual check to do in the React UI to confirm the feature renders correctly.
6. List the three most likely things that could be broken that the automated tests may not have caught.

Give me a checklist in order: run tests → fix any failures → manual spot-check → confirm done.
```

### Skill 5: `/write-tests`

Use this after implementing any backend layer to generate the tests for it.

Create `~/.claude/commands/write-tests.md`:

```markdown
I just implemented a feature. Now write the automated tests for it.

1. Read the feature code I just wrote (I will tell you which files).
2. Create or update `tests/factories.py` in the app — add a factory-boy factory for every new model, using SubFactory for any related models.
3. Write `tests/test_models.py` — test any model validation, custom save logic, or property methods.
4. Write `tests/test_views.py` — for each API endpoint, write:
   - One happy-path test (correct role, correct data → expected response)
   - One permission-denial test (wrong role → 403 or unauthenticated → 401)
   - One validation test (missing required field → 400 with an error message)
5. Show me only the test files. Do not touch any other file.
6. After writing the tests, tell me the exact command to run them.
```

---

## Step 23 — Understanding Claude Code's Built-In Modes

Claude Code has two important modes you should know:

### Plan Mode (`/plan`)

When you type `/plan` or ask Claude to "enter plan mode," it switches into a read-only exploration mode where it reads files and designs an approach — but writes no code. Use this at the start of any non-trivial feature.

**When to use it:** Before implementing any feature that touches more than 2-3 files. Ask Claude to plan first, review the plan, then say "go ahead."

### Agent Mode (spawned automatically)

For complex tasks like "explore the codebase" or "search for all files that reference Organisation," Claude Code automatically spawns a subagent to do the work without filling the main conversation with search results. You do not need to configure this — it just happens. But knowing it exists helps you write better prompts: broad exploration tasks are fine to ask for, because they get delegated.

---

---

# STAGE 4: Development Loop
## Repeated every working session until the product is done.

---

## The Loop at a Glance

```
Session Start
    ↓
Run /session-start → confirm active task
    ↓
Start local services (Docker, Django, React)
    ↓
Create a Git branch for the feature
    ↓
Run /feature-plan → review the plan → confirm
    ↓
Implement in layers: Model → Migration → Serializer → View → URL
    ↓
Run /write-tests → run pytest → fix any failures
    ↓
Run /verify → manual spot-check (curl, postgres MCP, browser)
    ↓
Commit working code (tests must pass)
    ↓
Session End → run /session-end → update MEMORY.md
    ↓
Repeat for next feature
```

---

## Step 24 — Session Start

Open a terminal in the project root:

```bash
source .venv/bin/activate
claude
```

Then in Claude Code, type:

```
/session-start
```

Read the response carefully. If Claude misidentifies the active task or the files it will touch, correct it before proceeding. This is the most important step — a misaligned start creates wasted work.

---

## Step 25 — Start Local Services

```bash
# Terminal 1 — PostgreSQL
docker compose up -d

# Terminal 2 — Django API
source .venv/bin/activate
python manage.py runserver

# Terminal 3 — React frontend
cd frontend && npm run dev
```

---

## Step 26 — Create a Feature Branch

Before any code is written, create a branch:

```bash
# Format: feature/fr-{number}-{short-description}
git checkout -b feature/fr-04-organisation-master-data
git checkout -b feature/fr-09-proforma-invoice-creation
git checkout -b fix/workflow-service-comment-validation
```

Your `main` branch stays clean.

---

## Step 27 — Plan the Feature Before Writing Code

In Claude Code:

```
02
z/feature-plan

The feature is FR-04: Organisation master data.
The relevant section in requirements.md is Section 5.3 (FR-04.1 through FR-04.4).
```

Read the plan. Check:
- Are the files it lists the right ones?
- Are there missing dependencies (e.g., Countries master must exist before Organisation can reference it)?
- Does it mention all four sub-sections: General Info, Tax Codes, Addresses, Role Tags?

Only say "go ahead" when the plan looks correct.

---

## Step 28 — Implement in Layers

This is the most important mental model for working with Claude Code on a full-stack project. **Build one layer at a time, verify it works, then move to the next.**

### The 7 Layers of a Backend Feature

```
Layer 1: Model          — The database table (apps/{app}/models.py)
Layer 2: Migration      — The SQL change (python manage.py makemigrations)
Layer 3: Serializer     — The API shape (apps/{app}/serializers.py)
Layer 4: View           — The endpoint logic (apps/{app}/views.py)
Layer 5: URL            — Wire it up (apps/{app}/urls.py → tradetocs/urls.py)
Layer 6: Tests          — Automated tests (apps/{app}/tests/)
Layer 7: Manual check   — Hit the endpoint with curl or a browser to confirm end-to-end
```

Write Layer 6 (tests) before doing the manual Layer 7 check. If tests pass, the manual check is a quick sanity check, not a full investigation.

### The 4 Layers of a Frontend Feature

```
Layer 1: API call file  — src/api/{resource}.ts
Layer 2: Page component — src/pages/{module}/{PageName}.tsx
Layer 3: Route          — Add to App.tsx
Layer 4: Manual test    — Open the browser, click through the form
```

### How to Prompt Claude for Each Layer

**Layer 1 (Model):**
```
Implement Layer 1 only: the Django model for Organisation.
Reference FR-04.1 through FR-04.4 in requirements.md for exact fields.
Apply constraint #5 (DecimalField), #7 (PROTECT on FKs), #8 (never hard-delete).
Show me only the models.py file. Do not touch anything else.
```

**Layer 2 (Migration):**
```
The model looks correct. Run makemigrations for the master_data app and show me the migration file.
```

(Then run `python manage.py migrate` yourself.)

**Layer 3 (Serializer):**
```
Implement Layer 3: the DRF serializer for Organisation.
Apply constraint #18: the serializer must be state-aware — fields that should not be editable
when the organisation is deactivated must be read_only.
Show me only the serializers.py file.
```

**Layer 4 (View):**
```
Implement Layer 4: the DRF view for Organisation CRUD.
Apply constraint #29: every view must explicitly declare permission_classes.
Checker and Company Admin can create/edit organisations. Maker can only read.
Show me only the views.py file.
```

**Layer 5 (URL):**
```
Implement Layer 5: register the Organisation endpoints in urls.py.
Use the URL structure from technical_architecture.md Section 5.
Show me only the urls.py changes.
```

**Layer 6 (Tests):**
```
/write-tests

The feature I just implemented is the Organisation CRUD (master_data app).
Files written: apps/master_data/models.py, serializers.py, views.py, urls.py.

Write:
- apps/master_data/tests/factories.py — OrganisationFactory with SubFactory for related models
- apps/master_data/tests/test_models.py — test is_active default, address FK, any custom validation
- apps/master_data/tests/test_views.py — for each endpoint:
    • Maker can list (GET 200), cannot create (POST 403)
    • Checker can create (POST 201), can edit (PATCH 200)
    • Unauthenticated gets 401

Show me only the test files. Then tell me the exact pytest command to run them.
```

After Claude writes the tests, run them:

```bash
source .venv/bin/activate
pytest apps/master_data/tests/ -v
```

If any tests fail, paste the full failure output to Claude and say: *"Diagnose the root cause. Do not write any fix yet."*

---

## Step 29 — Test and Verify Each Layer Before Moving On

After completing Layers 1–5 for a feature, do this in order:

**Step A — Write and run the tests (Layer 6):**

Use the `/write-tests` skill (see Step 28) to have Claude write the test files. Then run:

```bash
source .venv/bin/activate
pytest apps/{app}/tests/ -v
```

All tests must pass before you move on. If something fails, diagnose it — do not skip it or comment it out.

**Step B — Check coverage:**

```bash
pytest apps/{app}/tests/ --cov=apps/{app} --cov-report=term-missing
```

Look at the "Miss" column. If any critical code path (a view handler, a permission check) is uncovered, ask Claude to add a test for it.

**Step C — Manual spot-check (Layer 7):**

Run `/verify` or be specific:

```
I just wrote the Organisation model and ran migrations.
Using the postgres MCP, check the database and confirm:
1. The organisations_organisation table exists
2. It has all the columns defined in the model
3. The organisations_organisationaddress table exists with the correct foreign key
```

Manual checks catch things tests miss — visual layout, edge cases in the UI, end-to-end data flow across apps.

---

## Step 30 — Handling Errors

When Claude Code writes something that breaks, do not ask it to "just fix it." Be specific:

```bash
# Run the failing thing and copy the full error
python manage.py migrate
```

Then paste to Claude:

```
The migration failed with this error:
[paste the COMPLETE error output]

Diagnose the root cause only. Do not fix anything else.
Tell me what caused this before writing any fix.
```

Wait for the diagnosis. Confirm it makes sense. Then ask for the fix.

---

## Step 31 — Workflow Checklist Before Committing

Before committing any document-related code, verify all of the following:

**Tests (run this first — do not commit with failing tests):**
- [ ] `pytest` passes with 0 failures
- [ ] A happy-path test exists for each new endpoint
- [ ] A permission-denial test exists for each new endpoint (wrong role → 403, unauthenticated → 401)
- [ ] `pytest --cov=apps/{app}` shows no untested critical paths (view handlers, permission logic)

**Status transitions:**
- [ ] `status` is only ever assigned inside `apps/workflow/services.py`
- [ ] `transaction.atomic()` wraps both the status update and the AuditLog write

**Serializers:**
- [ ] Fields not editable in the current document state are dynamically set `read_only=True` in `__init__`

**PDF generation:**
- [ ] PDF is generated in memory and returned via `FileResponse` — no file is written to disk

**Frontend:**
- [ ] All Axios calls are in `src/api/*.ts` — no `axios` import in any component
- [ ] No status strings like `"DRAFT"` are hardcoded in component files

---

## Step 32 — Commit Working Code

```bash
git status
git diff                # review what actually changed

git add apps/master_data/
git add apps/master_data/migrations/
git commit -m "feat(fr-04): organisation model — addresses, tax codes, role tags"
git push origin feature/fr-04-organisation-master-data
```

**Commit message format:** `{type}({scope}): {description}`
- `feat(fr-04)`: new feature for FR-04
- `fix(workflow)`: bug fix in workflow service
- `refactor(serializers)`: serializer cleanup

---

## Step 33 — Session End

```
/session-end
```

Verify `memory/MEMORY.md` was updated before closing. This is how you carry context to the next session.

---

## Step 34 — Merge to Main When a Feature Is Done

When a feature is complete and manually verified:

```bash
git checkout main
git pull origin main
git merge feature/fr-04-organisation-master-data
git push origin main
git branch -d feature/fr-04-organisation-master-data
```

---

---

# STAGE 5: Feature Build Order
## What to build and in what order.

Each layer depends on the one before it. Do not start Layer 2 before Layer 1 is merged to main.

**Testing rule for all sessions:** After implementing a feature's backend layers, use `/write-tests` to generate the tests before moving to the next feature. Every session ends with `pytest` passing with 0 failures. Do not carry failing tests into the next session.

---

## Layer 1 — Foundation (no dependencies; build these first)

These are the tables and pages everything else depends on. Build them before touching any document.

| # | Feature | FR | Branch name |
| --- | --- | --- | --- |
| 1 | Project structure, settings, docker-compose, env | — | `feature/bootstrap` |
| 2 | `accounts` app — User model, JWT login/logout, roles, permission classes | — | `feature/accounts-auth` |
| 3 | `master_data` — lookup tables: Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy | FR-06 | `feature/fr-06-reference-data` |
| 4 | `master_data` — Organisation model (addresses, tax codes, role tags) | FR-04 | `feature/fr-04-organisation` |
| 5 | `master_data` — Bank model | FR-05 | `feature/fr-05-bank` |
| 6 | `master_data` — T&C Templates (rich text) | FR-07 | `feature/fr-07-tc-templates` |
| 7 | User Management page (Company Admin only) | FR-10 | `feature/fr-10-user-management` |
| 8 | All Master Data pages in React (Organisation, Bank, Reference Data, T&C Templates) | FR-04–07 and FR-10 | `feature/master-data-pages` |

**How to break Layer 1 into sessions:**
- Session 1: accounts app (User model + JWT auth). Write tests: login returns a token, wrong password returns 401, Maker cannot access admin endpoints. Stop. Confirm `pytest` passes.
- Session 2: Country, Port, Location, Incoterm, UOM, PaymentTerm, PreCarriageBy models + their API endpoints. Write tests: list endpoints return 200, unauthenticated gets 401. Confirm `pytest` passes.
- Session 3: Organisation model with all four sub-sections (FR-04.1–04.4). Write tests: factory for Organisation + Address, permission tests for Maker vs Checker. This is the most complex master data model. Give it a full session.
- Session 4: Bank model + API. Write tests. Confirm `pytest` passes.
- Session 5: T&C Template model + API. Write tests. Confirm `pytest` passes.
- Session 6: React pages for all master data (this is mostly CRUD forms — ask Claude to generate them one at a time).

---

## Layer 2 — Proforma Invoice (depends on Layer 1)

| # | Feature | FR | Branch name |
| --- | --- | --- | --- |
| 9 | PI model: header, line items, charges | FR-09.1–09.5 | `feature/fr-09-pi-model` |
| 10 | `workflow` app — WorkflowService, AuditLog (PI states first) | FR-08 | `feature/fr-08-workflow-pi` |
| 11 | PI create/edit API endpoints + state-aware serializers | FR-09 | `feature/fr-09-pi-api` |
| 12 | PI PDF generation (ReportLab) — DRAFT watermark + clean Approved output | FR-09.6 | `feature/fr-09-pi-pdf` |
| 13 | Proforma Invoice list, create, and detail pages (React) | FR-09 | `feature/fr-09-pi-pages` |

**How to break Layer 2 into sessions:**
- Session 1: PI model only. Run migration. Write model tests (field defaults, number format). Verify table in DB via postgres MCP.
- Session 2: WorkflowService for PI states (DRAFT → PENDING_APPROVAL → APPROVED → REWORK → PERMANENTLY_REJECTED). Write tests for every valid and invalid transition — e.g., APPROVED cannot go back to DRAFT, REJECT without a comment must raise an error. This is critical logic — spend a full session on it. Confirm `pytest` passes before moving on.
- Session 3: PI API endpoints (create, update, list, detail). Write permission tests (Maker cannot approve, unauthenticated gets 401). Verify with curl.
- Session 4: PI PDF layout in ReportLab. Generate a test PDF and open it.
- Session 5: React list and create pages.
- Session 6: React detail page (line items, workflow actions, PDF download).

---

## Layer 3 — Packing List (depends on Layer 2 — specifically on PI existing)

| # | Feature | FR | Branch name |
| --- | --- | --- | --- |
| 14 | PL model: header, containers, container items | FR-14.1–14.8 | `feature/fr-14-pl-model` |
| 15 | WorkflowService extended for PL states + cascade rules | FR-08 | `feature/fr-14-workflow-pl` |
| 16 | PL API endpoints (including copy-container) | FR-14 | `feature/fr-14-pl-api` |
| 17 | PL PDF generation | FR-14.10 | `feature/fr-14-pl-pdf` |
| 18 | Packing List form page in React (create + edit) | FR-14 | `feature/fr-14-pl-pages` |

---

## Layer 4 — Commercial Invoice (depends on Layer 3 — requires Approved Packing Lists)

| # | Feature | FR | Branch name |
| --- | --- | --- | --- |
| 19 | CI model: CommercialInvoice + CommercialInvoiceLineItem | FR-15 | `feature/fr-15-ci-model` |
| 20 | `CommercialInvoiceService.aggregate_line_items()` | FR-15.4 | `feature/fr-15-ci-aggregation` |
| 21 | WorkflowService extended for CI states (DISABLED terminal state) | FR-08 | `feature/fr-15-workflow-ci` |
| 22 | CI wizard API endpoints (eligible-consignees, approved-packing-lists, aggregate-line-items) | FR-15.1–15.6 | `feature/fr-15-ci-wizard-api` |
| 23 | CI PDF generation (Draft + Final modes) | FR-15.8 | `feature/fr-15-ci-pdf` |
| 24 | Commercial Invoice wizard page + detail page (React) | FR-15 | `feature/fr-15-ci-pages` |

---

## Layer 5 — Supporting Features (add after Layer 4)

| # | Feature | FR | Branch name |
| --- | --- | --- | --- |
| 25 | `SignedCopyUpload` model + upload/download endpoints | FR-08.4 | `feature/signed-copy-upload` |
| 26 | Audit log drawer (React, reusable across all three document types) | FR-08 | `feature/audit-log-drawer` |
| 27 | `reports` app — placeholder page | FR (OQ#4) | `feature/reports-placeholder` |

---

---

# QUICK REFERENCE: Prompt Templates

Copy-paste these in Claude Code.

---

### Start a new feature

```
/feature-plan

Feature: [paste the FR title and number]
Relevant requirements.md section: [section number, e.g., 5.3]
```

---

### Implement a single layer

```
Implement Layer [N] only: [what the layer is, e.g., "the Django model for PackingList"].
Reference requirements.md section [X] for exact fields.
Apply these constraints from technical_architecture.md Section 9: [list the relevant constraint numbers].
Show me only [the specific file]. Do not touch any other file.
```

---

### Write tests for a feature

```
/write-tests

Feature just implemented: [feature name, e.g., "Packing List CRUD"]
App: apps/[app_name]/
Files written: [list the files you just wrote]

Write the full test suite: factories.py, test_models.py, test_views.py.
Cover: happy path, permission denial (wrong role → 403), unauthenticated (401), and validation errors (400).
```

---

### Diagnose a failure

```
This command failed:
[command you ran]

Full error output:
[paste the complete error]

Tell me in plain English what caused this. Do not write any fix yet.
```

---

### Verify with the database

```
Using the postgres MCP, run a query to confirm:
[specific thing to check, e.g., "the packing_list_packinglist table has a proforma_invoice_id foreign key column"]
```

---

### Ask about a constraint

```
I am about to [describe what you're doing]. Does this violate any constraint in technical_architecture.md Section 9?
If yes, show me the correct way to do it.
```

---

---

# RECOVERY PROCEDURES

## When Claude Writes Code You Did Not Ask For

```
Stop. You changed [file X] which I did not ask you to touch.
Revert only [file X] to what it was before and explain why you changed it.
```

Then run:

```bash
git diff                    # see exactly what changed
git restore apps/the_file.py  # revert a specific file
```

---

## When Claude Breaks the Code and You Have Not Committed

```bash
git restore .
```

Resets every file to the last commit instantly.

---

## When Claude Breaks the Code and You Already Committed

```bash
git log --oneline           # find the bad commit hash
git revert HEAD             # creates a new commit that undoes the last one
```

---

## When Migrations Are Out of Sync

```bash
source .venv/bin/activate
python manage.py showmigrations          # see which are applied
python manage.py migrate --run-syncdb    # re-sync if tables are missing
```

Never run `--fake` unless you are absolutely certain the database schema already matches the migration.

---

## When Docker Will Not Start

```bash
docker compose logs
docker compose down
docker compose up -d --build
```

---

## When Claude Drifts Off Course

Use anchored corrections — point to the specific document and rule:

| What is happening | What to say |
| --- | --- |
| Claude is over-engineering | "Check requirements.md Section 2 Non-Goals. Is what you're building on that list?" |
| Claude used FloatField for money | "Check technical_architecture.md constraint #5. Fix it." |
| Claude updated status outside WorkflowService | "Check constraint #11. Move the status change into WorkflowService." |
| Claude hardcoded a status string | "Check constraints #10 and #23. Use the enum from constants.py." |
| Claude wrote PDF to disk | "Check constraint #20. Generate in memory and stream via FileResponse." |
| Claude is solving the wrong problem | "Check memory/MEMORY.md. What is the active task? Build only that." |

"You're overcomplicating this" has no anchor. The AI will not change course from vague feedback. Always point to a specific document and rule.

---

## The Complete Sequence at a Glance

| Stage | Step | Action |
| --- | --- | --- |
| **Machine Setup** | 1–7 | Install Homebrew, Git, GitHub SSH, OrbStack, Python, Node, Claude Code |
| **Project Bootstrap** | 8–18 | Create repo, scaffold Django + React, configure Docker, env, first migration |
| **Claude Code Power Setup** | 19 | Create `~/.claude/CLAUDE.md` (global rules) |
|  | 20 | Create `CLAUDE.md` in project root (TradeDocs rules) |
|  | 21 | Install PostgreSQL and Filesystem MCP servers |
|  | 22 | Create `/session-start`, `/session-end`, `/feature-plan`, `/verify`, `/write-tests` skills |
|  | 23 | Understand Plan Mode and Agent Mode |
| **Development Loop** | 24 | Run `/session-start` — confirm active task |
|  | 25 | Start Docker, Django, React |
|  | 26 | Create feature branch |
|  | 27 | Run `/feature-plan` — review and confirm before coding |
|  | 28 | Implement one layer at a time (model → migration → serializer → view → URL → tests → manual check) |
|  | 29 | Run `/write-tests` after Layer 5, then `pytest`, then `/verify` for manual spot-check |
|  | 30 | Handle errors with full error paste + diagnosis-first approach |
|  | 31 | Run workflow checklist before committing |
|  | 32 | Commit and push |
|  | 33 | Run `/session-end` — update MEMORY.md |
|  | 34 | Merge to main when feature is complete |
| **Feature Build Order** | — | Layer 1 (Foundation) → Layer 2 (PI) → Layer 3 (PL) → Layer 4 (CI) → Layer 5 (Supporting) |
