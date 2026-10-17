# ASCEND

A personal growth and development platform with a React/Vite frontend and a FastAPI backend. The backend stores goals, tasks, action plans, contributions, user accounts, and revocable login sessions in the existing SQLite database by default.

Authentication uses Argon2 password hashing and opaque, server-side sessions in an `HttpOnly` cookie. The browser never stores passwords or session tokens in local storage. Goal, task, milestone, progress, and contribution data is scoped to the signed-in account; challenge content remains demo content.

## Requirements

- Python 3.11 or newer
- PowerShell on Windows, or a shell with Python and `venv`

## Install and run on Windows

In one terminal, start the backend from the project root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The first run creates `backend/data/skills_to_impact.db`; existing database files are reused. The API is at <http://localhost:8000>; interactive API documentation is at <http://localhost:8000/docs>.

In a second terminal, start the frontend from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Vite is available at <http://localhost:5173>. It calls `http://localhost:8000` by default. To use another API URL, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL` before starting Vite.

If PowerShell blocks virtual-environment activation, either allow activation for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or run the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Configure

Copy `backend/.env.example` to `backend/.env` and adjust values as needed:

- `DATABASE_URL` defaults to a local SQLite file. For a Supabase PostgreSQL database, set it to a SQLAlchemy URL such as `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require`. Keep credentials in your local `.env`; do not commit them.
- `CORS_ORIGINS` is a comma-separated list and defaults to `http://localhost:5173` and `http://127.0.0.1:5173` for Vite's local hostnames.
- `AUTH_COOKIE_SECURE` defaults to `false` for local HTTP development. Set it to `true` for HTTPS deployments.
- `AUTH_COOKIE_SAMESITE` defaults to `lax`. Use `none` only for a cross-site frontend/backend deployment and only with `AUTH_COOKIE_SECURE=true`; `strict` is also supported.
- `AUTH_SESSION_DAYS` sets the absolute session lifetime (1–365 days; default 14). Logging out revokes the session in the database and expires the browser cookie.
- `VITE_API_BASE_URL` (optional, in `frontend/.env`) selects the API URL; it defaults to `http://localhost:8000`. Do not put secrets in Vite environment variables because frontend values are public.
- The session cookie uses a cryptographically random opaque token; only its SHA-256 digest is stored in the database. No signing secret is needed or hardcoded.
Plan generation is deterministic and runs locally; the application does not call an AI provider or send goal data to an external planning service.

Database tables are created automatically at startup. The additive schema update creates user/session tables, adds a default status to existing goals, and adds nullable `user_id` columns to existing goals and contributions; task and milestone ownership follows the owning goal. Existing records are retained with a null owner and are intentionally hidden from every account until an operator explicitly assigns them to the correct user. This avoids exposing a previous user's data to the first person who registers. Back up the database and verify ownership before performing any manual reassignment. For production deployments and future schema evolution, use a versioned migration tool such as Alembic.

Email addresses are normalized to lowercase and unique. Signup requires a name, a valid email, matching passwords of at least 12 characters with uppercase, lowercase, number, and symbol. Login errors do not reveal whether an email is registered. The API also checks browser `Origin` values on write requests against `CORS_ORIGINS`.

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness status |
| POST | `/auth/signup` | Register an account and start a session |
| POST | `/auth/login` | Verify credentials and start a session |
| GET | `/auth/me` | Return the current user's public profile |
| POST | `/auth/logout` | Revoke the current session and clear its cookie |
| POST, GET | `/goals` | Create and list goals |
| GET, PATCH, DELETE | `/goals/{goal_id}` | Read, update, and delete a goal |
| GET | `/goals/{goal_id}/plan` | Read saved milestones, scheduled tasks, source, and next action |
| POST | `/goals/{goal_id}/plan` | Generate or update a plan; use `{"force": true}` only after confirming unfinished generated actions will be archived |
| POST, GET | `/tasks` | Create and list tasks; `goal_id` is an optional list filter |
| PATCH, DELETE | `/tasks/{task_id}` | Update and delete a task |
| GET | `/challenges` | List demo community challenges |
| GET | `/challenges/{challenge_id}` | Read a demo community challenge |
| POST, GET | `/contributions` | Create and list contributions |
| GET, DELETE | `/contributions/{contribution_id}` | Read and delete a contribution |
| GET | `/progress` | Calculate progress from stored goals and tasks |

All account, goal, task, plan, contribution, and progress endpoints require the session cookie. Resource lookups are scoped to the current user and return `404` for another account's records. The API validates request bodies. Plan tasks and milestones belong to their goal, have ordered target dates and task schedules, estimates, and completion criteria, and are persisted alongside completion state. Repeated generation is rejected unless an update is explicitly requested. Updating a plan archives superseded unfinished generated actions (retaining their database records), keeps completed and manually added tasks, and creates a coherent replacement plan. Archived actions are excluded from the active task list and progress totals; completed actions from earlier plans remain visible as completed unassigned actions. Goal titles are duplicate-checked case-insensitively within each account. Progress is calculated from stored records; it is not an invented statistic.

## Run tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests use a temporary in-memory SQLite database and do not depend on the development database file. Frontend validation commands are:

```powershell
cd frontend
npm run lint
npm run build
```
