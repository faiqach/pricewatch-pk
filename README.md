# PriceWatch PK
AI-powered commodity price tracking and overpricing alert system for Pakistan built with FastAPI, Flutter, PostgreSQL, and AI forecasting.

## Backend setup

The backend is a FastAPI application with SQLAlchemy ORM, PostgreSQL support, Alembic migrations, and seed data.

### Setup

1. Create and activate a Python environment.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Create a PostgreSQL database named `pricewatch_pk`.
4. Copy `backend/.env.example` to `backend/.env` and update the database connection string.
5. Run migrations:
   ```bash
   alembic upgrade head
   ```
6. Seed data:
   ```bash
   python -m backend.app.db.seed
   ```
7. Start the API:
   ```bash
   uvicorn main:app --reload --app-dir backend
   ```

### API health check

- `GET /health`
