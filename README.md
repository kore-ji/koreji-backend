# Koreji Backend

FastAPI backend application with PostgreSQL database, Alembic migrations, and Docker containerization.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

### 1. Start the Application

```bash
make all
```

This will:
- Build Docker images
- Start PostgreSQL and FastAPI services
- Run database migrations automatically
- Enable hot reload for development

**Access Points:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 2. Stop the Application

```bash
make stop    # Stop containers, keep data
```

or press `Ctrl-C` if running in foreground.

### 3. Resume Work

```bash
make up      # Restart with existing data
```

## Available Commands

### Main Operations

```bash
make all        # Build and start everything (default)
make up         # Start services in background
make stop       # Stop containers (keeps data)
make down       # Stop and remove containers (keeps volumes)
make clean      # Remove everything including database data
```

### Development

```bash
make logs       # Follow live logs (Ctrl-C to stop)
make logs-tail  # Show last 100 log lines
```

### Database & Migrations

```bash
make migrate    # Manually run migrations (usually not needed)
```

## Project Structure

```
koreji-backend/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # Database configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── user.py
│   └── users/               # Users module
│       ├── router.py        # API endpoints
│       ├── service.py       # Business logic
│       └── schemas.py       # Pydantic schemas
├── alembic/                 # Database migrations
│   ├── env.py
│   └── versions/
├── docker-compose.yaml      # Service orchestration
├── Dockerfile               # Container definition
├── entrypoint.sh           # Container startup script
├── requirements.txt         # Python dependencies
├── alembic.ini             # Alembic configuration
└── Makefile                # Development commands
```

## Database Migrations

Migrations run **automatically** when containers start. For manual migration management:

### Create a New Migration

1. Modify or add models in `src/models/`
2. Generate migration script:

```bash
# Inside the container
docker-compose exec koreji-backend alembic revision --autogenerate -m "description"

# Or from host (if alembic installed locally)
alembic revision --autogenerate -m "description"
```

3. Review the generated file in `alembic/versions/`
4. Restart containers to apply:

```bash
make up
```

### Manual Migration Commands

```bash
# Apply migrations
docker-compose exec koreji-backend alembic upgrade head

# Rollback one migration
docker-compose exec koreji-backend alembic downgrade -1

# View migration history
docker-compose exec koreji-backend alembic history

# Check current version
docker-compose exec koreji-backend alembic current
```

## Development

### Hot Reload

Code changes in `src/` are automatically detected and reload the server.

### View Logs

```bash
# Follow all logs
make logs

# Show recent logs
make logs-tail

# Follow specific service
docker-compose logs -f koreji-backend
docker-compose logs -f postgres
```

### Access Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U koreji -d koreji_db

# Common queries
\dt                    # List tables
\d users               # Describe users table
SELECT * FROM users;   # Query users
```

## Environment Variables

Set in `docker-compose.yaml`:

- `DATABASE_URL` - PostgreSQL connection string
- `PYTHONUNBUFFERED` - Python output buffering (set to 1)

For local development without Docker, create a `.env` file:

```env
DATABASE_URL=postgresql://koreji:koreji_password@localhost:5432/koreji_db
```

## Production Considerations

For production deployment:

1. Change `fastapi dev` to `fastapi run` in `entrypoint.sh`
2. Set proper environment variables
3. Use secrets management for credentials
4. Configure proper logging
5. Set up reverse proxy (nginx/traefik)
6. Enable HTTPS
7. Configure CORS properly
8. Set up monitoring and health checks
