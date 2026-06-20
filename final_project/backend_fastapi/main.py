from fastapi import FastAPI, Depends, File, HTTPException, UploadFile, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from pathlib import Path
from typing import List, Optional
import shutil
import uuid

from database import get_db, get_connection
import crud
from schemas import (
    CompanyCreate, CompanyUpdate, CompanyResponse,
    JobCreate, JobUpdate, JobResponse,
    ApplicationCreate, ApplicationResponse,
    UserCreate, UserResponse, TokenResponse
)
from auth import create_access_token, verify_token, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI(
    title="Project Job API",
    description="FastAPI backend with Oracle 11g for Job Portal",
    version="1.0.0"
)

RESUME_UPLOAD_DIR = Path(__file__).resolve().parent / "uploads" / "resumes"


def _object_exists(cur, object_type: str, object_name: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM user_objects WHERE object_type = :1 AND object_name = :2",
        [object_type.upper(), object_name.upper()],
    )
    return cur.fetchone()[0] > 0


def _table_columns(cur, table_name: str) -> dict:
    cur.execute(
        "SELECT column_name, data_type FROM user_tab_columns WHERE table_name = :1",
        [table_name.upper()],
    )
    return {row[0].upper(): row[1].upper() for row in cur.fetchall()}


def _ensure_sequence(cur, sequence_name: str):
    if not _object_exists(cur, "SEQUENCE", sequence_name):
        cur.execute(f"CREATE SEQUENCE {sequence_name} START WITH 1 INCREMENT BY 1")


def _ensure_column(cur, columns: dict, table_name: str, column_name: str, definition: str):
    normalized = column_name.upper()
    if normalized not in columns:
        cur.execute(f"ALTER TABLE {table_name} ADD {column_name} {definition}")
        columns[normalized] = definition.split()[0].upper()


def init_db():
    """Create or lightly migrate Oracle tables used by this API."""
    with get_connection() as conn:
        cur = conn.cursor()

        # Companies
        _ensure_sequence(cur, "companies_seq")
        if not _object_exists(cur, "TABLE", "companies"):
            cur.execute(
                "CREATE TABLE companies (id NUMBER PRIMARY KEY, name VARCHAR2(255), description CLOB, website VARCHAR2(255))"
            )
        else:
            company_columns = _table_columns(cur, "companies")
            _ensure_column(cur, company_columns, "companies", "description", "CLOB")
            _ensure_column(cur, company_columns, "companies", "website", "VARCHAR2(255)")

        # Jobs
        _ensure_sequence(cur, "jobs_seq")
        if not _object_exists(cur, "TABLE", "jobs"):
            cur.execute(
                "CREATE TABLE jobs (id NUMBER PRIMARY KEY, title VARCHAR2(255), description CLOB, location VARCHAR2(255), salary VARCHAR2(100), company_id NUMBER, posted_date TIMESTAMP, is_active VARCHAR2(1) CHECK (is_active IN ('Y', 'N')), posted_by VARCHAR2(255))"
            )
        else:
            job_columns = _table_columns(cur, "jobs")
            _ensure_column(cur, job_columns, "jobs", "salary", "VARCHAR2(100)")
            _ensure_column(cur, job_columns, "jobs", "posted_date", "TIMESTAMP")
            _ensure_column(cur, job_columns, "jobs", "is_active", "VARCHAR2(1)")
            _ensure_column(cur, job_columns, "jobs", "posted_by", "VARCHAR2(255)")

            if "SALARY_MIN" in job_columns or "SALARY_MAX" in job_columns:
                cur.execute(
                    """
                    UPDATE jobs
                    SET salary =
                        CASE
                            WHEN salary_min IS NOT NULL AND salary_max IS NOT NULL
                                THEN TO_CHAR(salary_min) || ' - ' || TO_CHAR(salary_max)
                            WHEN salary_min IS NOT NULL THEN TO_CHAR(salary_min)
                            WHEN salary_max IS NOT NULL THEN TO_CHAR(salary_max)
                            ELSE salary
                        END
                    WHERE salary IS NULL
                    """
                )

            if "PUBLISHED_AT" in job_columns and "CREATED_AT" in job_columns:
                date_source = "CAST(NVL(published_at, created_at) AS TIMESTAMP)"
            elif "PUBLISHED_AT" in job_columns:
                date_source = "CAST(published_at AS TIMESTAMP)"
            elif "CREATED_AT" in job_columns:
                date_source = "CAST(created_at AS TIMESTAMP)"
            else:
                date_source = "SYSTIMESTAMP"
            cur.execute(f"UPDATE jobs SET posted_date = {date_source} WHERE posted_date IS NULL")

            if "STATUS" in job_columns:
                cur.execute(
                    """
                    UPDATE jobs
                    SET is_active =
                        CASE
                            WHEN UPPER(status) IN ('CLOSED', 'INACTIVE', 'N') THEN 'N'
                            ELSE 'Y'
                        END
                    WHERE is_active IS NULL
                    """
                )
            else:
                cur.execute("UPDATE jobs SET is_active = 'Y' WHERE is_active IS NULL")

            if "RECRUITER_ID" in job_columns and _object_exists(cur, "TABLE", "users"):
                cur.execute(
                    """
                    UPDATE jobs j
                    SET posted_by = (
                        SELECT u.username
                        FROM users u
                        WHERE u.id = j.recruiter_id
                    )
                    WHERE posted_by IS NULL
                    AND EXISTS (
                        SELECT 1
                        FROM users u
                        WHERE u.id = j.recruiter_id
                    )
                    """
                )

        # Users
        _ensure_sequence(cur, "users_seq")
        if not _object_exists(cur, "TABLE", "users"):
            cur.execute(
                "CREATE TABLE users (id NUMBER PRIMARY KEY, username VARCHAR2(255), email VARCHAR2(255), hashed_password VARCHAR2(255), is_active VARCHAR2(1) CHECK (is_active IN ('Y', 'N')))"
            )

        # Resumes
        _ensure_sequence(cur, "resumes_seq")
        if not _object_exists(cur, "TABLE", "resumes"):
            cur.execute(
                "CREATE TABLE resumes (id NUMBER PRIMARY KEY, filename VARCHAR2(255), stored_path VARCHAR2(500), content_type VARCHAR2(150), uploaded_by VARCHAR2(255), uploaded_at TIMESTAMP)"
            )

        # Applications
        _ensure_sequence(cur, "applications_seq")
        if not _object_exists(cur, "TABLE", "applications"):
            cur.execute(
                "CREATE TABLE applications (id NUMBER PRIMARY KEY, job_id NUMBER, candidate_id NUMBER, status VARCHAR2(50), applied_at TIMESTAMP, updated_at TIMESTAMP, cover_letter CLOB, resume_url VARCHAR2(500), notes CLOB)"
            )
        else:
            application_columns = _table_columns(cur, "applications")
            _ensure_column(cur, application_columns, "applications", "candidate_id", "NUMBER")
            _ensure_column(cur, application_columns, "applications", "cover_letter", "CLOB")
            _ensure_column(cur, application_columns, "applications", "resume_url", "VARCHAR2(500)")
            _ensure_column(cur, application_columns, "applications", "notes", "CLOB")
            if "RESUME_PATH" in application_columns:
                cur.execute(
                    "UPDATE applications SET resume_url = resume_path WHERE resume_url IS NULL AND resume_path IS NOT NULL"
                )

        conn.commit()


@app.on_event("startup")
def startup_event():
    try:
        init_db()
    except Exception:
        pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def root():
    return {"message": "Project Job API", "docs": "/docs"}


# ============= Auth Routes =============

@app.post("/api/auth/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate):
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    db_email = crud.get_user_by_email(user.email)
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(user)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    user_payload = {"id": user['id'], "username": user['username'], "email": user['email'], "is_active": user['is_active']}
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_payload
    }


# ============= Company Routes =============

@app.get("/api/companies", response_model=List[CompanyResponse])
def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get all companies with pagination"""
    return crud.get_companies(skip, limit)


@app.post("/api/companies", response_model=CompanyResponse, status_code=201)
def create_company(
    company: CompanyCreate,
    token: str = Depends(verify_token),
):
    """Create a new company (auth required)"""
    return crud.create_company(company)


@app.get("/api/companies/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: int,
):
    """Get company by ID"""
    company = crud.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.put("/api/companies/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: int,
    company: CompanyUpdate,
    token: str = Depends(verify_token),
):
    """Update company by ID (auth required)"""
    db_company = crud.update_company(company_id, company)
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    return db_company


@app.delete("/api/companies/{company_id}", status_code=204)
def delete_company(
    company_id: int,
    token: str = Depends(verify_token),
):
    """Delete company by ID (auth required)"""
    company = crud.delete_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")


# ============= Job Routes =============

@app.get("/api/jobs", response_model=List[JobResponse])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    company_id: Optional[int] = Query(None),
):
    """Get all jobs with search and filtering"""
    return crud.get_jobs(skip, limit, search, company_id)


@app.post("/api/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job: JobCreate,
    token: str = Depends(verify_token),
):
    """Create a new job (auth required)"""
    if job.company_id and not crud.get_company(job.company_id):
        raise HTTPException(status_code=404, detail="Company not found")
    return crud.create_job(job, token)


@app.get("/api/recruiter/jobs", response_model=List[JobResponse])
def list_recruiter_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(verify_token),
):
    """Get jobs posted by the current recruiter."""
    return crud.get_jobs_for_recruiter(token, skip, limit)


@app.get("/api/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
):
    """Get job by ID"""
    job = crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job: JobUpdate,
    token: str = Depends(verify_token),
):
    """Update job by ID (auth required)"""
    db_job = crud.update_job_for_recruiter(job_id, job, token)
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job


@app.delete("/api/jobs/{job_id}", status_code=204)
def delete_job(
    job_id: int,
    token: str = Depends(verify_token),
):
    """Delete job by ID (auth required)"""
    job = crud.delete_job_for_recruiter(job_id, token)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")


# ============= Resume Routes =============

@app.post("/api/resumes/upload", status_code=201)
def upload_resume(
    file: UploadFile = File(...),
    token: str = Depends(verify_token),
):
    """Upload a resume file (auth required)."""
    allowed_extensions = {".pdf", ".doc", ".docx"}
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()

    if not original_name or extension not in allowed_extensions:
        raise HTTPException(status_code=422, detail="Upload a PDF, DOC, or DOCX resume file")

    RESUME_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = RESUME_UPLOAD_DIR / stored_name

    with stored_path.open("wb") as output_file:
        shutil.copyfileobj(file.file, output_file)

    resume = crud.create_resume(
        filename=original_name,
        stored_path=str(stored_path),
        content_type=file.content_type or "application/octet-stream",
        username=token,
    )
    return {"message": "Resume uploaded successfully", "resume": resume}


# ============= Application Routes =============

@app.post("/api/applications", response_model=ApplicationResponse, status_code=201)
def create_application(
    application: ApplicationCreate,
    token: str = Depends(verify_token),
):
    """Apply to a job (auth required)."""
    job = crud.get_job(application.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("is_active") is False:
        raise HTTPException(status_code=400, detail="This job is closed")

    user = crud.get_user_by_username(token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = crud.get_application_by_user_and_job(user["id"], application.job_id)
    if existing:
        raise HTTPException(status_code=400, detail="You have already applied to this job")

    return crud.create_application(application, user["id"])


@app.get("/api/applications/me", response_model=List[ApplicationResponse])
def list_my_applications(
    token: str = Depends(verify_token),
):
    """List applications for the current user."""
    user = crud.get_user_by_username(token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_applications_for_user(user["id"])


@app.get("/api/applications", response_model=List[ApplicationResponse])
def list_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(verify_token),
):
    """List all applications (auth required)."""
    return crud.get_applications(skip, limit)


@app.get("/api/recruiter/applications", response_model=List[ApplicationResponse])
def list_recruiter_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    token: str = Depends(verify_token),
):
    """List applications for jobs posted by the current recruiter."""
    return crud.get_applications_for_recruiter(token, skip, limit)
