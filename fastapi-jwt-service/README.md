# FastAPI JWT Auth Microservice

REST API with user registration, login, and protected CRUD. Passwords are hashed with bcrypt, access is via JWT Bearer tokens, payloads are validated with Pydantic, and data lives in SQLite (PostgreSQL-ready).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then set a strong SECRET_KEY
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs  |  ReDoc: http://127.0.0.1:8000/redoc

Generate a secret key: `python -c "import secrets; print(secrets.token_hex(32))"`

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /auth/register | No | Create account |
| POST | /auth/login | No | Get JWT (form fields: username=email, password) |
| GET | /auth/me | Bearer | Current user |
| POST | /items/ | Bearer | Create item |
| GET | /items/ | Bearer | List your items (skip, limit) |
| GET | /items/{id} | Bearer | Get one item |
| PUT | /items/{id} | Bearer | Update item |
| DELETE | /items/{id} | Bearer | Delete item |
| GET | /health | No | Health check |

## Tests

```bash
pytest -v
```

## Switching to PostgreSQL

`pip install psycopg2-binary`, then set `DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/dbname` in `.env`.
