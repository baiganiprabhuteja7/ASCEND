# Skills to Impact API

A local FastAPI backend for the Skills to Impact frontend. Data is stored in SQLite by default. The database URL is configurable through environment variables, and SQLAlchemy keeps the persistence layer replaceable without changing the API routes.

This project does **not** implement authentication or a live community. The challenge catalog is clearly labeled demo content. Goal action plans are saved in SQLite; they use the configured backend LLM when it returns a valid plan, and otherwise use a clearly labeled deterministic fallback.

## Requirements

- Python 3.11 or newer
- PowerShell on Windows, or a shell with Python and `venv`

## Install and run on Windows

From the project root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The first run creates `backend/data/skills_to_impact.db`. The API is at <http://localhost:8000>; interactive API documentation is at <http://localhost:8000/docs>.

If PowerShell blocks virtual-environment activation, either allow activation for the current terminal with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, or run the environment's executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Configure

Copy `.env.example` to `.env` and adjust values as needed:

- `DATABASE_URL` defaults to a local SQLite file. For a Supabase PostgreSQL database, set it to a SQLAlchemy URL such as `postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require`. Keep credentials in your local `.env`; do not commit them.
- `CORS_ORIGINS` is a comma-separated list and defaults to `http://localhost:5173`.
- `LLM_API_KEY` is optional and used only by the backend. For Gemini, create a key in Google AI Studio and set it only in `backend/.env`. Leave it blank to use the deterministic fallback planner.
- `LLM_BASE_URL` defaults to Gemini's documented OpenAI-compatible endpoint, `https://generativelanguage.googleapis.com/v1beta/openai/`.
- `LLM_MODEL` defaults to `gemini-3.8-flash`. Model access can vary by project; select a model listed for your key and supported by Gemini's OpenAI-compatible endpoint.
- The backend loads `backend/.env` relative to its configuration file, regardless of the current working directory. `LLM_API_KEY` is read only by the backend, and its configured status can be checked without exposing its value.
- `LLM_TIMEOUT_SECONDS` sets the response timeout and `LLM_CONNECT_TIMEOUT_SECONDS` sets the connection timeout. HTTP 429/503 responses are retried at most once, using a bounded delay and a reasonable `Retry-After` value when provided. Other provider failures and invalid responses fall back to the built-in planner. Diagnostics include the provider status and a sanitized message or exception type; API keys and authorization values are not logged.

When Gemini is configured, the backend sends the goal title, description, skill level, learning preferences, weekly availability, and deadline to draft a plan. The response is parsed and validated against the existing Pydantic plan schema before scheduling or persistence. Invalid output and provider errors use the deterministic fallback, which the Action Plan page labels as such. Leave `LLM_API_KEY` blank to keep plan generation local. Never put the key in frontend code or return it from an API.

To verify a real Gemini request manually, set a valid key in `backend/.env`, restart the backend, create a test goal with a future deadline, and generate its plan once from the Action Plan page. The goal should show **AI-assisted plan** if the provider response passes validation, or **Deterministic fallback plan** if it does not. This makes a real API request and may use quota; automated tests use mocked responses and do not contact Gemini.

Database tables are created automatically at startup. A small additive migration adds the planning columns and milestone table to an existing SQLite database while retaining legacy goals and tasks. For production deployments, add a migration tool such as Alembic before evolving the schema.

## API endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Liveness status |
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

The API validates request bodies and returns `404` for missing resources. Plan tasks and milestones belong to their goal, have ordered target dates and task schedules, estimates, and completion criteria, and are persisted alongside completion state. Repeated generation is rejected unless an update is explicitly requested. Updating a plan archives superseded unfinished generated actions (retaining their database records), keeps completed and manually added tasks, and creates a coherent replacement plan. Archived actions are excluded from the active task list and progress totals; completed actions from earlier plans remain visible as completed unassigned actions. Goal titles are duplicate-checked case-insensitively to reduce accidental duplicate goals; existing duplicate records are retained. Progress is calculated from stored records; it is not an invented statistic.

## Run tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

Tests use a temporary in-memory SQLite database and do not depend on the development database file.
