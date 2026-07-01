# OPulse FastAPI Backend

OPulse is an AI-powered productivity platform designed to help students and professionals optimize their study and work schedules. This backend is built using **Clean Architecture** patterns, ensuring high scalability, testability, and separation of concerns.

---

## Technical Stack & Features
- **FastAPI**: Modern, high-performance web framework.
- **PostgreSQL**: Robust primary database.
- **SQLAlchemy (2.0 Async)**: Async ORM mapping.
- **Alembic**: Database schema migrations tool.
- **APScheduler**: Asynchronous background jobs dispatcher (used for reminder scans).
- **Custom AI Recommendation Engine**: Deterministic weighted scoring system recommending tasks based on deadline urgency, priority weight, focus durations, historical completions, daily productivity timeframes, overdue status, and recurrence.
- **Pluggable AI Design**: Abstract interfaces (`BaseRecommendationEngine`, etc.) that allow swapping the heuristic scoring engine with LLM services (Gemini, Ollama, OpenAI) later without changing routers or API contracts.
- **Activity Log Audit**: Automatic logging of creation, completion, edits, and reminder interactions to drive AI insights.
- **Comprehensive Pytest Suite**: Full integration test coverage for authentication, task lifecycle, analytics, and AI logic.
- **Docker Ready**: Multistage production `Dockerfile` and `docker-compose.yml`.

---

## Directory Structure Walkthrough
```
C:/Users/Samruddhi/.gemini/antigravity/scratch/opulse-backend/
├── app/
│   ├── core/             # Base configurations (Database, Security, Logging configs)
│   ├── dependencies/     # Router dependency injection providers (auth filters, session yields)
│   ├── models/           # Declarative DB models (User, Task, Category, Reminder, ActivityLog) & Enums
│   ├── schemas/          # Input/Output validation Pydantic schemas (DTOs)
│   ├── repositories/     # Database access layer (Generic CRUD & specific queries)
│   ├── services/         # Core business logic layer (Auth, CRUD, Analytics aggregates)
│   │   └── ai/           # Pluggable AI modules (recommendation, priority, productivity engines)
│   ├── jobs/             # Scheduled background jobs (APScheduler engine)
│   ├── routers/          # API route controllers, versioned under /api/v1/
│   ├── utils/            # General helper scripts (recurrence due dates incrementer)
│   └── main.py           # Application bootstrapper
├── migrations/           # Database migration versions
├── tests/                # Pytest suites
└── docker-compose.yml    # PostgreSQL and Backend orchestration service
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11+
- PostgreSQL database (or Docker installed)

### 2. Local Setup
Clone the repository and initialize a virtual environment:
```bash
# Initialize virtualenv
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt aiosqlite
```

Create a `.env` file in the root folder:
```env
PROJECT_NAME="OPulse AI Platform"
ENV="development"
API_V1_STR="/api/v1"

# JWT configuration (Run: openssl rand -hex 32 to generate a new key)
SECRET_KEY="supersecretkeythatisverysecureandlongerthanthirtytwobytesforhashing"
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Connection details (Local)
POSTGRES_SERVER="localhost"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DB="opulse"
POSTGRES_PORT=5432
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/opulse"
```

### 3. Run Migrations
Initialize database schemas:
```bash
alembic upgrade head
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.
- **API Documentation**: `http://127.0.0.1:8000/api/v1/docs` (Swagger UI)
- **ReDoc Documentation**: `http://127.0.0.1:8000/api/v1/redoc`

---

## Running with Docker

Orchestrate the app and PostgreSQL instance instantly:
```bash
# Build and run containers
docker-compose up --build
```
This runs postgres under container name `opulse-db` and boots the FastAPI server at port `8000` with hot-reload mapped.

---

## Running Tests

Execute the comprehensive test suite locally (uses isolated in-memory SQLite):
```bash
python -m pytest
```
Tests cover:
1. **Authentication**: Register, login, refresh tokens, and protect filters.
2. **Tasks & Recurrence**: CRUD, category validations, and auto-spawning of next task due dates upon completing recurring items.
3. **Analytics**: Completion ratios, study streak tracking, and focus scores math.
4. **AI Services**: Score weight calculations, urgency tags, daily study plans, and productivity insights.
