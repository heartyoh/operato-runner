# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python)
```bash
# Install dependencies (uv recommended)
uv pip install -r requirements.txt
# or: pip install -r requirements.txt

# Run the main server
python main.py
# Custom configuration:
python main.py --config=./modules.yaml --rest-port=8080 --grpc-port=50052 --venv-path=./custom_venvs

# Database migrations (Alembic)
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade base

# Run tests
pytest
pytest tests/specific_test.py
pytest -v  # verbose
pytest --cov  # with coverage

# Test single test
pytest tests/test_executor.py::test_inline_executor -v
```

### Frontend (React TypeScript)
```bash
cd admin-ui

# Install dependencies
npm install

# Development server
npm start  # runs on port 3000 with proxy to localhost:8000

# Build for production
npm run build

# Run tests
npm test
```

### Docker Development
```bash
# Full stack (with PostgreSQL & Redis)
docker-compose up -d

# Minimal stack (SQLite only)
docker-compose -f docker-compose-minimal.yml up -d

# Backend only with database migration
docker-compose up backend

# View logs
docker-compose logs -f backend
```

## Architecture Overview

**Operato Runner** is a multi-execution environment platform for safely running Python modules with REST API and gRPC interfaces.

### Core Components

1. **Execution Environments** (`executors/`)
   - `inline.py` - Direct execution in current process
   - `venv.py` - Python virtual environment execution  
   - `conda.py` - Conda environment execution
   - `docker.py` - Docker container execution
   - `uv.py` - UV virtual environment execution (ultra-fast)

2. **Module Management** (`models/`, `schemas/`)
   - Module registration and versioning
   - Environment variable management
   - Execution history tracking
   - User authentication & authorization (RBAC)

3. **API Layer** (`api/`)
   - `rest.py` - FastAPI REST API server
   - `grpc_server.py` - gRPC service implementation
   - `auth.py` - JWT-based authentication
   - `routes/modules.py` - Module-specific routes

4. **Database Layer** (`models/`, `core/db.py`)
   - SQLAlchemy async ORM
   - SQLite (development) / PostgreSQL (production) support
   - Alembic migrations
   - Models: Module, User, Version, Deployment, AuditLog, etc.

5. **Admin UI** (`admin-ui/`)
   - React TypeScript frontend
   - Material-UI components
   - Module management, user management, execution monitoring

### Key Patterns

- **Executor Pattern**: All execution environments implement `executors.base.Executor` interface
- **Registry Pattern**: `ModuleRegistry` manages module lifecycle and metadata
- **Manager Pattern**: `ExecutorManager` coordinates between different executors
- **Repository Pattern**: Database models with async SQLAlchemy sessions
- **Dependency Injection**: FastAPI dependencies for authentication and database sessions

### Module Structure Requirements

Python modules uploaded to the platform must include:
- `handler.py` - Entry point with `handler(input: dict) -> dict` function
- `requirements.txt` - Python dependencies
- Optional: `__main__.py` for direct execution

### Configuration

- `modules.yaml` - Module definitions (inline code or file paths)
- `.env` - Environment variables (DATABASE_URL, REDIS_URL, JWT secrets)
- `alembic.ini` - Database migration configuration
- Docker Compose files for different deployment scenarios

### Testing Strategy

- `tests/conftest.py` - Test configuration with automatic Alembic migrations
- Unit tests for executors, models, API endpoints
- Integration tests for end-to-end module execution
- Test database isolation with SQLite

### Security Features

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Audit logging for all operations
- Environment variable encryption for sensitive data

The platform supports both development (SQLite + local execution) and production (PostgreSQL + Redis + Docker) environments.