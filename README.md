HEAD
# ASCEND

ASCEND is a personal growth platform for setting goals, turning them into scheduled actions, and tracking progress from saved work. It is an existing React/Vite frontend backed by a FastAPI API and SQLAlchemy database.

## Features

- Account signup/login with Argon2 password hashing and revocable, `HttpOnly` cookie sessions.
- Account-scoped goal, task, milestone, contribution, and progress data.
- Create, edit, update status, and delete goals; create, edit, complete, and delete tasks.
- Deterministic, local action-plan generation based on goals, skill level, schedule, learning preferences, and availability. No generative AI or external planning service is used.
- Database-backed progress and goal-status summaries.
- React Router navigation and protected application pages.

## Requirements

- Python 3.11 or newer
- Node.js 20.19+ or 22.12+ (Vite 8 requirement)
- npm

## Run locally on Windows

Open two PowerShell terminals from the repository root.

### Backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is at <http://localhost:8000>, health check at <http://localhost:8000/health>, and interactive OpenAPI documentation at <http://localhost:8000/docs>.

### Frontend

```powershell
cd frontend
npm ci
npm run dev
```

Open the Vite URL printed in the terminal (normally <http://localhost:5173>). The frontend uses `http://localhost:8000` by default. Set `VITE_API_BASE_URL` in `frontend/.env` if the API runs at a different URL.

If PowerShell blocks environment activation, use the Python executable directly from `backend`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Configuration and data

Copy `backend/.env.example` to `backend/.env` for backend settings. `DATABASE_URL` defaults to `sqlite:///./data/skills_to_impact.db`, resolved relative to the backend working directory. The frontend's `VITE_API_BASE_URL` is optional; frontend environment values are public and must not contain secrets.

`CORS_ORIGINS` defaults to both `http://localhost:5173` and `http://127.0.0.1:5173`. For HTTPS deployments, configure `AUTH_COOKIE_SECURE=true`; `SameSite=None` requires secure cookies. Keep `.env` files private. Existing database records and local configuration should be backed up before any manual migration or reassignment.

The startup migration preserves existing records, adds goal status to existing rows, and keeps legacy unowned records hidden from signed-in accounts until ownership is explicitly assigned. The default database is local SQLite.

## Validation

Run the backend test suite:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Run frontend lint and production build:

```powershell
cd frontend
npm run lint
npm run build
```

Backend tests use temporary in-memory SQLite databases and do not modify the local development database.

## Project layout

- `backend/app/` — FastAPI application, schemas, SQLAlchemy models, auth, routes, and local plan generation.
- `backend/tests/` — API, authentication, validation, migration, and planning tests.
- `frontend/src/` — React pages, reusable components, styles, and API client.
=======
# ASCEND 🚀
### A Personal Growth and Development Platform

ASCEND is a personal growth and development platform designed to help individuals improve their skills, work toward their goals, and turn learning into meaningful action.

## 📌 About the Project

ASCEND aims to bridge the gap between personal development and real-world impact. It focuses on helping individuals grow continuously, develop useful skills, and make consistent progress toward their goals.

The project follows a modular architecture, separating the frontend and backend for better organization and maintainability.

## ✨ Key Highlights

- Personal growth and continuous learning
- Organized frontend and backend architecture
- Goal-oriented development approach
- Designed with future improvements in mind
- Ongoing software development project

## 🛠️ Tech Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python
- **Version Control:** Git and GitHub

> Update this section if your actual implementation uses additional frameworks, databases, or technologies.

## 📂 Project Structure

```text
ASCEND/
├── backend/
└── frontend/
```

## ⚙️ Getting Started

### Prerequisites

- Git
- Python
- A modern web browser

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/baiganiprabhuteja7/ASCEND.git
   ```

2. Navigate to the project directory:

   ```bash
   cd ASCEND
   ```

3. Explore the `frontend` and `backend` directories.

4. Follow the setup instructions and install the dependencies required by each component.

### Running the Application

Refer to the frontend and backend setup instructions to start the application. Add the exact commands here once the project setup has been verified.

## 🚧 Project Status

ASCEND is under active development. Features, functionality, and documentation will evolve as development progresses.

## 🔮 Future Improvements

- Enhance the user experience
- Expand personal development features
- Improve backend functionality
- Add testing and error handling
- Improve deployment and documentation

## 👨‍💻 Author

**Prabhu Teja**

GitHub: [baiganiprabhuteja7](https://github.com/baiganiprabhuteja7)

---

*Building technology that supports continuous growth and meaningful progress.*
>>>>>>> bda038bd651134d9c48481cdc638e93a8c449466
