# FastAPI + Oracle 11g Backend for Project Job

## Quick Start

### 1. Create and activate virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables



**CMD:**
```cmd
set ORACLE_USER=your_user
set ORACLE_PASSWORD=your_password
set ORACLE_HOST=oracle-host
set ORACLE_PORT=1521
set ORACLE_SERVICE=ORCLPDB1
set SECRET_KEY=change-me
```

Or use `ORACLE_DSN` directly:
```
set ORACLE_DSN=host:port/service_name
```

### 4. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://127.0.0.1:8000/docs

## API Endpoints

### Authentication
- **POST** `/api/auth/register` — Register a new user
  - Body: `username`, `password`, `email`
  - Response: User object

- **POST** `/api/auth/login` — Login and get JWT token
  - Body: `username`, `password`
  - Response: `access_token`, `token_type`, `user`

### Companies
- **GET** `/api/companies` — List all companies
  - Query params: `skip`, `limit`

- **POST** `/api/companies` — Create company (auth required)
  - Body: `name`, `description`, `website`

- **GET** `/api/companies/{company_id}` — Get company details

- **PUT** `/api/companies/{company_id}` — Update company (auth required)
  - Body: `name`, `description`, `website`

- **DELETE** `/api/companies/{company_id}` — Delete company (auth required)

### Jobs
- **GET** `/api/jobs` — List all jobs
  - Query params: `skip`, `limit`, `search`, `company_id`

- **POST** `/api/jobs` — Create job (auth required)
  - Body: `title`, `description`, `location`, `salary`, `company_id`, `is_active`

- **GET** `/api/jobs/{job_id}` — Get job details

- **PUT** `/api/jobs/{job_id}` — Update job (auth required)
  - Body: `title`, `description`, `location`, `salary`, `company_id`, `is_active`

- **DELETE** `/api/jobs/{job_id}` — Delete job (auth required)

## Project Structure

```
backend_fastapi/
├── main.py           # FastAPI app and routes
├── database.py       # Oracle connection and session
├── models.py         # SQLAlchemy models
├── schemas.py        # Pydantic schemas
├── crud.py           # CRUD operations
├── auth.py           # JWT and auth utilities
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Database Notes

- Uses the `oracledb` driver for Oracle 11g connectivity.

- Oracle 11g/XE requires python-oracledb Thick mode. The dependency is pinned to
  `oracledb>=2.0,<3.0` so the bundled Oracle XE 11.2 client can be used.

- If you install a newer python-oracledb major version, use Oracle Instant Client
  19 and set `ORACLE_CLIENT_LIB_DIR` to that directory. Instant Client 21/23 will
  not connect to Oracle 11g.

- On this common local XE install, the backend auto-detects:
  `C:\oraclexe\app\oracle\product\11.2.0\server\bin`

- To refresh an existing virtual environment after changing dependencies:

```bash
python -m pip install -r requirements.txt --upgrade
```

## Authentication

- JWT tokens in `Authorization: Bearer <token>` header.
- Token expires in 60 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
- Protected endpoints require valid token.
