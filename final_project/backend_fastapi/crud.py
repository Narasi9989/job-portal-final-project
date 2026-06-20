import oracledb
from database import get_connection
from passlib.context import CryptContext
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _table_columns(cur, table_name: str) -> Dict[str, str]:
    cur.execute(
        "SELECT column_name, data_type FROM user_tab_columns WHERE table_name = :1",
        [table_name.upper()],
    )
    return {row[0].upper(): row[1].upper() for row in cur.fetchall()}


def _table_exists(cur, table_name: str) -> bool:
    cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", [table_name])
    if cur.fetchone()[0]:
        return True
    cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = :1", [table_name.upper()])
    return cur.fetchone()[0] > 0


def _insert_row(cur, table_name: str, values: Dict[str, Any], expressions: Dict[str, str] = None):
    expressions = expressions or {}
    columns = []
    placeholders = []
    params = {}

    for column, value in values.items():
        columns.append(column.lower())
        param_name = f"p{len(params) + 1}"
        placeholders.append(f":{param_name}")
        params[param_name] = value

    for column, expression in expressions.items():
        columns.append(column.lower())
        placeholders.append(expression)

    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
    cur.execute(sql, params)


def _safe_text(value, default: str) -> str:
    return value if value not in (None, "") else default


def _active_insert_value(columns: Dict[str, str]):
    return 1 if columns.get("IS_ACTIVE") == "NUMBER" else "Y"


def _inactive_insert_value(columns: Dict[str, str]):
    return 0 if columns.get("IS_ACTIVE") == "NUMBER" else "N"


def _user_id_for_username(cur, username: str):
    cur.execute("SELECT id FROM users WHERE username = :1", [username])
    row = cur.fetchone()
    return int(row[0]) if row else None


def _ensure_legacy_user(cur, user_id: int, role: str) -> Optional[int]:
    if not user_id or not _table_exists(cur, "user"):
        return None

    cur.execute(
        "SELECT id, username, email, hashed_password, is_active FROM users WHERE id = :1",
        [user_id],
    )
    user_row = cur.fetchone()
    if not user_row:
        return None

    username = user_row[1]
    email = user_row[2]
    hashed_password = user_row[3]
    is_active = 1 if _active_to_bool(user_row[4]) else 0
    legacy_role = "employer" if role == "employer" else "jobseeker"

    cur.execute('SELECT id, username FROM "user" WHERE id = :1', [user_id])
    legacy_row = cur.fetchone()
    if legacy_row and legacy_row[1] == username:
        return int(legacy_row[0])

    cur.execute('SELECT id FROM "user" WHERE username = :1 OR email = :2', (username, email))
    legacy_row = cur.fetchone()
    if legacy_row:
        return int(legacy_row[0])

    if not legacy_row:
        if not legacy_row and user_id:
            cur.execute('SELECT COUNT(*) FROM "user" WHERE id = :1', [user_id])
            use_same_id = cur.fetchone()[0] == 0
        else:
            use_same_id = False

        if use_same_id:
            legacy_id = user_id
        else:
            cur.execute('SELECT NVL(MAX(id), 0) + 1 FROM "user"')
            legacy_id = int(cur.fetchone()[0])

        cur.execute(
            'INSERT INTO "user" (id, username, email, hashed_password, role, is_active) '
            'VALUES (:1, :2, :3, :4, :5, :6)',
            (legacy_id, username, email, hashed_password, legacy_role, is_active),
        )
        return legacy_id

    return None


def _ensure_legacy_job(cur, job_id: int) -> Optional[int]:
    if not job_id or not _table_exists(cur, "JOB") or not _table_exists(cur, "user"):
        return None

    cur.execute(
        """
        SELECT j.id, j.title, j.description, j.location, j.posted_by, c.name
        FROM jobs j
        LEFT JOIN companies c ON j.company_id = c.id
        WHERE j.id = :1
        """,
        [job_id],
    )
    job_row = cur.fetchone()
    if not job_row:
        return None

    posted_by = job_row[4]
    employer_user_id = _user_id_for_username(cur, posted_by) if posted_by else None
    legacy_employer_id = _ensure_legacy_user(cur, employer_user_id, "employer") if employer_user_id else None
    if not legacy_employer_id:
        cur.execute('SELECT id FROM "user" WHERE role = :1 AND ROWNUM = 1', ["employer"])
        row = cur.fetchone()
        legacy_employer_id = int(row[0]) if row else None

    if not legacy_employer_id:
        return None

    now_text = datetime.utcnow().isoformat()
    title = _safe_text(job_row[1], "Untitled job")
    description = _safe_text(_read_lob(job_row[2]), "No description provided")
    location = _safe_text(job_row[3], "Not specified")
    company = _safe_text(job_row[5], "Company")

    cur.execute("SELECT COUNT(*) FROM job WHERE id = :1", [job_id])
    if cur.fetchone()[0]:
        cur.execute(
            """
            UPDATE job
            SET title = :1,
                description = :2,
                location = :3,
                category = :4,
                company = :5,
                employer_id = :6,
                updated_at = :7
            WHERE id = :8
            """,
            (title, description, location, "General", company, legacy_employer_id, now_text, job_id),
        )
    else:
        cur.execute(
            """
            INSERT INTO job (id, title, description, location, category, company, employer_id, created_at, updated_at)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            """,
            (job_id, title, description, location, "General", company, legacy_employer_id, now_text, now_text),
        )
    return job_id


def _read_lob(value):
    if hasattr(value, "read"):
        return value.read()
    return value


def _bool_to_flag(value):
    return "Y" if value else "N"


def _flag_to_bool(value):
    if isinstance(value, str):
        return value.upper() == "Y"
    return bool(value)


def _active_to_bool(value):
    if isinstance(value, str):
        return value.upper() in ("Y", "1", "TRUE")
    return bool(value)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# --- Company CRUD using direct SQL ---
def get_company(company_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, website FROM companies WHERE id = :id", [company_id])
        row = cur.fetchone()
        if not row:
            return None
        return {"id": int(row[0]), "name": row[1], "description": _read_lob(row[2]), "website": row[3]}


def get_companies(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, website FROM companies ORDER BY id")
        rows = cur.fetchall()
        result = []
        for r in rows:
            result.append({"id": int(r[0]), "name": r[1], "description": _read_lob(r[2]), "website": r[3]})
        return result[skip: skip + limit]


def create_company(data) -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT companies_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        columns = _table_columns(cur, "companies")
        values = {"ID": new_id, "NAME": data.name}
        if "DESCRIPTION" in columns:
            values["DESCRIPTION"] = data.description
        if "WEBSITE" in columns:
            values["WEBSITE"] = data.website
        expressions = {}
        if "CREATED_AT" in columns:
            expressions["CREATED_AT"] = "SYSDATE"
        if "UPDATED_AT" in columns:
            expressions["UPDATED_AT"] = "SYSDATE"
        _insert_row(cur, "companies", values, expressions)
        conn.commit()
        return {"id": new_id, "name": data.name, "description": data.description, "website": data.website}


def update_company(company_id: int, data) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM companies WHERE id = :id", [company_id])
        if not cur.fetchone():
            return None
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            cur.execute(f"UPDATE companies SET {key} = :1 WHERE id = :2", (value, company_id))
        conn.commit()
        return get_company(company_id)


def delete_company(company_id: int) -> Optional[Dict[str, Any]]:
    company = get_company(company_id)
    if not company:
        return None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM companies WHERE id = :id", [company_id])
        conn.commit()
    return company


def get_or_create_recruiter_company(username: str) -> Dict[str, Any]:
    company_name = f"{username} hiring"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, description, website FROM companies WHERE name = :1", [company_name])
        row = cur.fetchone()
        if row:
            return {"id": int(row[0]), "name": row[1], "description": _read_lob(row[2]), "website": row[3]}

        cur.execute("SELECT companies_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        columns = _table_columns(cur, "companies")
        values = {"ID": new_id, "NAME": company_name}
        if "DESCRIPTION" in columns:
            values["DESCRIPTION"] = "Recruiter posted jobs"
        if "WEBSITE" in columns:
            values["WEBSITE"] = None
        expressions = {}
        if "CREATED_AT" in columns:
            expressions["CREATED_AT"] = "SYSDATE"
        if "UPDATED_AT" in columns:
            expressions["UPDATED_AT"] = "SYSDATE"
        _insert_row(cur, "companies", values, expressions)
        conn.commit()
        return {"id": new_id, "name": company_name, "description": "Recruiter posted jobs", "website": None}


# --- Job CRUD using direct SQL ---
def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT j.id, j.title, j.description, j.location, j.salary, j.company_id, j.posted_date, j.is_active, j.posted_by, c.id, c.name, c.description, c.website FROM jobs j LEFT JOIN companies c ON j.company_id = c.id WHERE j.id = :id", [job_id])
        row = cur.fetchone()
        if not row:
            return None
        company = None
        if row[9] is not None:
            company = {"id": int(row[9]), "name": row[10], "description": _read_lob(row[11]), "website": row[12]}
        return {"id": int(row[0]), "title": row[1], "description": _read_lob(row[2]), "location": row[3], "salary": row[4], "company": company, "company_id": int(row[5]) if row[5] is not None else None, "posted_date": row[6], "is_active": _flag_to_bool(row[7]), "posted_by": row[8]}


def get_jobs(skip: int = 0, limit: int = 100, search: str = None, company_id: int = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        sql = "SELECT j.id, j.title, j.description, j.location, j.salary, j.company_id, j.posted_date, j.is_active, j.posted_by, c.id, c.name, c.description, c.website FROM jobs j LEFT JOIN companies c ON j.company_id = c.id"
        params = []
        if search:
            sql += " WHERE (LOWER(j.title) LIKE :s OR LOWER(j.description) LIKE :s)"
            params.append(f"%{search.lower()}%")
            if company_id:
                sql += " AND j.company_id = :cid"
                params.append(company_id)
        elif company_id:
            sql += " WHERE j.company_id = :cid"
            params.append(company_id)
        sql += " ORDER BY j.posted_date DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        result = []
        for row in rows:
            company = None
            if row[9] is not None:
                company = {"id": int(row[9]), "name": row[10], "description": _read_lob(row[11]), "website": row[12]}
            result.append({
                "id": int(row[0]), "title": row[1], "description": _read_lob(row[2]), "location": row[3], "salary": row[4],
                "company": company, "company_id": int(row[5]) if row[5] is not None else None, "posted_date": row[6], "is_active": _flag_to_bool(row[7]), "posted_by": row[8]
            })
        return result[skip: skip + limit]


def get_jobs_for_recruiter(username: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT j.id FROM jobs j WHERE j.posted_by = :1 ORDER BY j.posted_date DESC",
            [username],
        )
        rows = cur.fetchall()
        return [get_job(int(row[0])) for row in rows][skip: skip + limit]


def create_job(data, posted_by: str) -> Dict[str, Any]:
    company_id = data.company_id
    if not company_id:
        company_id = get_or_create_recruiter_company(posted_by)["id"]

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT jobs_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        columns = _table_columns(cur, "jobs")
        recruiter_id = _user_id_for_username(cur, posted_by)
        active = bool(data.is_active)

        values = {
            "ID": new_id,
            "TITLE": _safe_text(data.title, "Untitled job"),
        }
        if "DESCRIPTION" in columns:
            values["DESCRIPTION"] = _safe_text(data.description, "No description provided")
        if "LOCATION" in columns:
            values["LOCATION"] = _safe_text(data.location, "Not specified")
        if "SALARY" in columns:
            values["SALARY"] = data.salary
        if "COMPANY_ID" in columns:
            values["COMPANY_ID"] = company_id
        if "IS_ACTIVE" in columns:
            values["IS_ACTIVE"] = _bool_to_flag(active)
        if "POSTED_BY" in columns:
            values["POSTED_BY"] = posted_by
        if "CATEGORY" in columns:
            values["CATEGORY"] = "General"
        if "STATUS" in columns:
            values["STATUS"] = "OPEN" if active else "CLOSED"
        if "RECRUITER_ID" in columns:
            values["RECRUITER_ID"] = recruiter_id

        expressions = {}
        if "POSTED_DATE" in columns:
            expressions["POSTED_DATE"] = "SYSTIMESTAMP"
        if "PUBLISHED_AT" in columns:
            expressions["PUBLISHED_AT"] = "SYSDATE"
        if "CREATED_AT" in columns:
            expressions["CREATED_AT"] = "SYSDATE"
        if "UPDATED_AT" in columns:
            expressions["UPDATED_AT"] = "SYSDATE"

        _insert_row(cur, "jobs", values, expressions)
        _ensure_legacy_job(cur, new_id)
        conn.commit()
        return get_job(new_id)


def update_job(job_id: int, data) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM jobs WHERE id = :id", [job_id])
        if not cur.fetchone():
            return None
        columns = _table_columns(cur, "jobs")
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'company_id':
                cur.execute("UPDATE jobs SET company_id = :1 WHERE id = :2", (value, job_id))
            elif key == 'is_active':
                if "IS_ACTIVE" in columns:
                    cur.execute("UPDATE jobs SET is_active = :1 WHERE id = :2", (_bool_to_flag(value), job_id))
                if "STATUS" in columns:
                    cur.execute("UPDATE jobs SET status = :1 WHERE id = :2", ("OPEN" if value else "CLOSED", job_id))
            else:
                cur.execute(f"UPDATE jobs SET {key} = :1 WHERE id = :2", (value, job_id))
        if "UPDATED_AT" in columns:
            cur.execute("UPDATE jobs SET updated_at = SYSDATE WHERE id = :1", [job_id])
        conn.commit()
        return get_job(job_id)


def update_job_for_recruiter(job_id: int, data, username: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    if not job or job.get("posted_by") != username:
        return None
    return update_job(job_id, data)


def delete_job(job_id: int) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    if not job:
        return None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jobs WHERE id = :id", [job_id])
        conn.commit()
    return job


def delete_job_for_recruiter(job_id: int, username: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    if not job or job.get("posted_by") != username:
        return None
    return delete_job(job_id)


# --- Resume CRUD ---
def create_resume(filename: str, stored_path: str, content_type: str, username: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT resumes_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        cur.execute(
            "INSERT INTO resumes (id, filename, stored_path, content_type, uploaded_by, uploaded_at) "
            "VALUES (:1, :2, :3, :4, :5, SYSTIMESTAMP)",
            (new_id, filename, stored_path, content_type, username),
        )
        conn.commit()
        return {
            "id": new_id,
            "filename": filename,
            "stored_path": stored_path,
            "content_type": content_type,
            "uploaded_by": username,
        }


# --- Application CRUD ---
def get_application_by_user_and_job(candidate_id: int, job_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, job_id, candidate_id, status, applied_at, cover_letter, resume_url, notes FROM applications "
            "WHERE candidate_id = :1 AND job_id = :2",
            (candidate_id, job_id),
        )
        row = cur.fetchone()
        if not row:
            return None
        notes = _parse_application_notes(row[7])
        return {
            "id": int(row[0]),
            "job_id": int(row[1]),
            "candidate_id": int(row[2]),
            "status": row[3],
            "applied_at": row[4],
            "cover_letter": _read_lob(row[5]),
            "resume_url": row[6],
            **notes,
        }


def _application_notes(applicant_name: str, experience: str, skills: str) -> str:
    return json.dumps({
        "applicant_name": applicant_name,
        "experience": experience,
        "skills": skills,
    })


def _parse_application_notes(value) -> Dict[str, Any]:
    raw = _read_lob(value)
    if not raw:
        return {"applicant_name": None, "experience": None, "skills": None}
    try:
        data = json.loads(raw)
        return {
            "applicant_name": data.get("applicant_name"),
            "experience": data.get("experience"),
            "skills": data.get("skills"),
        }
    except (TypeError, ValueError):
        return {"applicant_name": None, "experience": None, "skills": raw}


def create_application(data, candidate_id: int) -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        _ensure_legacy_job(cur, data.job_id)
        cur.execute("SELECT applications_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        notes = _application_notes(data.applicant_name, data.experience, data.skills)
        columns = _table_columns(cur, "applications")
        values = {
            "ID": new_id,
            "JOB_ID": data.job_id,
            "STATUS": "Applied",
        }
        if "CANDIDATE_ID" in columns:
            values["CANDIDATE_ID"] = candidate_id
        if "USER_ID" in columns:
            values["USER_ID"] = _ensure_legacy_user(cur, candidate_id, "jobseeker") or candidate_id
        if "COVER_LETTER" in columns:
            values["COVER_LETTER"] = data.cover_letter
        if "RESUME_URL" in columns:
            values["RESUME_URL"] = data.resume_url
        if "RESUME_PATH" in columns:
            values["RESUME_PATH"] = _safe_text(data.resume_url, "not-provided")
        if "NOTES" in columns:
            values["NOTES"] = notes

        expressions = {}
        if "APPLIED_AT" in columns:
            expressions["APPLIED_AT"] = "SYSDATE"
        if "UPDATED_AT" in columns:
            expressions["UPDATED_AT"] = "SYSDATE"
        if "CREATED_AT" in columns:
            expressions["CREATED_AT"] = "SYSDATE"

        _insert_row(cur, "applications", values, expressions)
        conn.commit()
        application = get_application_by_user_and_job(candidate_id, data.job_id)
        return application


def get_applications_for_user(candidate_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, job_id, candidate_id, status, applied_at, cover_letter, resume_url, notes FROM applications "
            "WHERE candidate_id = :1 ORDER BY applied_at DESC",
            [candidate_id],
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            job = get_job(int(row[1]))
            notes = _parse_application_notes(row[7])
            result.append({
                "id": int(row[0]),
                "job_id": int(row[1]),
                "candidate_id": int(row[2]),
                "status": row[3],
                "applied_at": row[4],
                "cover_letter": _read_lob(row[5]),
                "resume_url": row[6],
                **notes,
                "job": job,
            })
        return result


def get_applications(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, job_id, candidate_id, status, applied_at, cover_letter, resume_url, notes FROM applications ORDER BY applied_at DESC"
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            job = get_job(int(row[1]))
            notes = _parse_application_notes(row[7])
            result.append({
                "id": int(row[0]),
                "job_id": int(row[1]),
                "candidate_id": int(row[2]),
                "status": row[3],
                "applied_at": row[4],
                "cover_letter": _read_lob(row[5]),
                "resume_url": row[6],
                **notes,
                "job": job,
            })
        return result[skip: skip + limit]


def get_applications_for_recruiter(username: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT a.id, a.job_id, a.candidate_id, a.status, a.applied_at, a.cover_letter, a.resume_url, a.notes "
            "FROM applications a JOIN jobs j ON a.job_id = j.id "
            "WHERE j.posted_by = :1 ORDER BY a.applied_at DESC",
            [username],
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            job = get_job(int(row[1]))
            notes = _parse_application_notes(row[7])
            result.append({
                "id": int(row[0]),
                "job_id": int(row[1]),
                "candidate_id": int(row[2]),
                "status": row[3],
                "applied_at": row[4],
                "cover_letter": _read_lob(row[5]),
                "resume_url": row[6],
                **notes,
                "job": job,
            })
        return result[skip: skip + limit]


# --- User CRUD ---
def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, hashed_password, is_active FROM users WHERE username = :u", [username])
        row = cur.fetchone()
        if not row:
            return None
        return {"id": int(row[0]), "username": row[1], "email": row[2], "hashed_password": row[3], "is_active": _active_to_bool(row[4])}


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, email, hashed_password, is_active FROM users WHERE email = :e", [email])
        row = cur.fetchone()
        if not row:
            return None
        return {"id": int(row[0]), "username": row[1], "email": row[2], "hashed_password": row[3], "is_active": _active_to_bool(row[4])}


def create_user(user) -> Dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT users_seq.NEXTVAL FROM dual")
        new_id = int(cur.fetchone()[0])
        hashed = get_password_hash(user.password)
        columns = _table_columns(cur, "users")
        values = {
            "ID": new_id,
            "USERNAME": user.username,
            "EMAIL": user.email,
            "HASHED_PASSWORD": hashed,
        }
        if "IS_ACTIVE" in columns:
            values["IS_ACTIVE"] = _active_insert_value(columns)
        if "ROLE" in columns:
            values["ROLE"] = "user"

        expressions = {}
        if "CREATED_AT" in columns:
            expressions["CREATED_AT"] = "SYSDATE"
        if "UPDATED_AT" in columns:
            expressions["UPDATED_AT"] = "SYSDATE"

        _insert_row(cur, "users", values, expressions)
        conn.commit()
        return {"id": new_id, "username": user.username, "email": user.email, "is_active": True}


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if not user:
        user = get_user_by_email(username)
    if not user:
        return None
    if not verify_password(password, user['hashed_password']):
        return None
    return user
