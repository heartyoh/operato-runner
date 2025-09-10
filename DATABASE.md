# Database Configuration Guide

Operato Runner supports multiple database backends with automatic driver conversion between async and sync operations.

## Quick Start

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Choose your database configuration in `.env`:

## Supported Databases

### SQLite (Development)
```bash
# Local file database - ideal for development
DATABASE_URL=sqlite+aiosqlite:///./app.db

# In-memory database - for testing
DATABASE_URL=sqlite+aiosqlite:///:memory:
```

**Pros**: No setup required, portable
**Cons**: Single connection, limited concurrency

### PostgreSQL (Production)
```bash
# Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/operato

# Docker Compose PostgreSQL
DATABASE_URL=postgresql+asyncpg://operato:operato123@postgres:5432/operato

# Production PostgreSQL with SSL
DATABASE_URL=postgresql+asyncpg://user:pass@prod.example.com:5432/operato?sslmode=require
```

**Pros**: Full ACID compliance, excellent performance, production-ready
**Cons**: Requires setup

### MySQL (Alternative)
```bash
# Local MySQL
DATABASE_URL=mysql+aiomysql://username:password@localhost:3306/operato

# Docker MySQL
DATABASE_URL=mysql+aiomysql://operato:operato123@mysql:3306/operato
```

**Pros**: Wide compatibility, good performance
**Cons**: Less PostgreSQL-compatible features

## Database Migration

### First-time Setup
```bash
# Initialize database with migrations
alembic upgrade head
```

### Creating New Migrations
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Database Switching
The system automatically handles driver conversion:

- **Application** (FastAPI): Uses async drivers (`+asyncpg`, `+aiosqlite`, `+aiomysql`)
- **Migrations** (Alembic): Uses sync drivers (`+psycopg2`, `sqlite`, `+pymysql`)

## Environment Examples

### Development (.env)
```bash
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

### Production (.env)
```bash
DATABASE_URL=postgresql+asyncpg://operato:operato123@postgres:5432/operato
JWT_SECRET_KEY=your-production-secret-key
REDIS_URL=redis://redis:6379/0
```

### Docker Compose
Uses environment variable substitution:
```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
```

Set `DATABASE_URL` in your host `.env` file or Docker environment.

## Troubleshooting

### Connection Issues
1. Verify database server is running
2. Check credentials and host/port
3. Ensure required drivers are installed:
   ```bash
   # PostgreSQL
   pip install asyncpg psycopg2-binary
   
   # MySQL  
   pip install aiomysql PyMySQL
   
   # SQLite (included)
   pip install aiosqlite
   ```

### Migration Issues
1. Check if database is accessible
2. Verify Alembic can connect:
   ```bash
   alembic check
   ```
3. For SQLite permission issues:
   ```bash
   chmod 666 app.db
   ```

### Database-Specific Features
- **UUID columns**: Automatically use appropriate type per database
- **Timestamps**: Auto-configured (`datetime('now')` for SQLite, `NOW()` for others)
- **JSON columns**: PostgreSQL native, MySQL JSON, SQLite TEXT fallback

## Performance Tips

### SQLite
- Use WAL mode: `DATABASE_URL=sqlite+aiosqlite:///./app.db?wal=true`
- Set busy timeout: `DATABASE_URL=sqlite+aiosqlite:///./app.db?timeout=20`

### PostgreSQL
- Use connection pooling in production
- Enable logging for query optimization
- Consider read replicas for high-traffic applications

### MySQL
- Use utf8mb4 charset for full UTF-8 support
- Configure appropriate timeouts for long-running queries