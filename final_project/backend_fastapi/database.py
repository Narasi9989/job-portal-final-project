import os
import glob
import oracledb
from contextlib import contextmanager

# Oracle connection configuration
ORACLE_USER = os.environ.get("ORACLE_USER", "narasimha")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD", "narasimha")
ORACLE_HOST = os.environ.get("ORACLE_HOST", "localhost")
ORACLE_PORT = os.environ.get("ORACLE_PORT", "1521")
ORACLE_SERVICE = os.environ.get("ORACLE_SERVICE", "XE")
ORACLE_DSN = os.environ.get("ORACLE_DSN", "")
ORACLE_CONFIG_DIR = os.environ.get(
    "ORACLE_CONFIG_DIR",
    os.path.join(os.path.dirname(__file__), "oracle_config"),
)
ORACLE_USE_THICK_MODE = os.environ.get("ORACLE_USE_THICK_MODE", "true").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


def _normalize_client_dir(path):
    """Return the directory containing oci.dll, if the path looks usable."""
    if not path:
        return None

    expanded = os.path.abspath(os.path.expandvars(os.path.expanduser(path)))
    if os.path.isfile(os.path.join(expanded, "oci.dll")):
        return expanded

    bin_dir = os.path.join(expanded, "bin")
    if os.path.isfile(os.path.join(bin_dir, "oci.dll")):
        return bin_dir

    if os.path.isdir(expanded):
        return expanded
    return None


def _discover_client_lib_dir():
    configured = os.environ.get("ORACLE_CLIENT_LIB_DIR") or os.environ.get("ORACLE_HOME")
    candidates = []
    if configured:
        candidates.append(configured)

    # Prefer clients that can connect to Oracle 11g before newer clients.
    for pattern in (
        r"C:\instantclient_19*",
        r"C:\instantclient_18*",
        r"C:\instantclient_12*",
        r"C:\instantclient_11*",
        r"C:\oraclexe\app\oracle\product\11.2.0\server\bin",
        r"C:\instantclient_21*",
        r"C:\instantclient_23*",
    ):
        candidates.extend(sorted(glob.glob(pattern), reverse=True))

    seen = set()
    for candidate in candidates:
        client_dir = _normalize_client_dir(candidate)
        if client_dir and client_dir.lower() not in seen:
            seen.add(client_dir.lower())
            return client_dir
    return None


ORACLE_CLIENT_LIB_DIR = _discover_client_lib_dir()


def _init_oracle_client():
    if not ORACLE_USE_THICK_MODE:
        return

    if hasattr(oracledb, "is_thin_mode") and not oracledb.is_thin_mode():
        return

    if not ORACLE_CLIENT_LIB_DIR:
        raise RuntimeError(
            "Oracle 11g/XE requires python-oracledb Thick mode. Install Oracle "
            "Instant Client 19, or set ORACLE_CLIENT_LIB_DIR to an existing Oracle "
            "client directory that contains oci.dll."
        )

    try:
        kwargs = {"lib_dir": ORACLE_CLIENT_LIB_DIR}
        if ORACLE_CONFIG_DIR and os.path.isdir(ORACLE_CONFIG_DIR):
            kwargs["config_dir"] = ORACLE_CONFIG_DIR

        oracledb.init_oracle_client(**kwargs)
        print(f"Oracle client initialized from {ORACLE_CLIENT_LIB_DIR}")
    except Exception as e:
        raise RuntimeError(
            "Could not initialize python-oracledb Thick mode from "
            f"{ORACLE_CLIENT_LIB_DIR}. For Oracle 11g/XE, install dependencies from "
            "backend_fastapi/requirements.txt so python-oracledb stays below 3.0, "
            "or use Oracle Instant Client 19 and set ORACLE_CLIENT_LIB_DIR to it. "
            f"Original error: {e}"
        ) from e


_init_oracle_client()

# Build DSN
if ORACLE_DSN:
    DSN = ORACLE_DSN
elif ORACLE_SERVICE:
    DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"
else:
    DSN = ""

# Create a connection pool on import
_pool = None
if DSN and ORACLE_USER and ORACLE_PASSWORD:
    try:
        _pool = oracledb.create_pool(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=DSN,
            min=1,
            max=5,
            increment=1
        )
    except Exception as e:
        print(f"Warning: Could not create connection pool: {e}")
        _pool = None


@contextmanager
def get_connection():
    """Context manager that yields an oracledb connection from the pool (or a direct connection)."""
    conn = None
    try:
        if _pool:
            conn = _pool.acquire()
        else:
            conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=DSN)
        yield conn
    finally:
        try:
            if conn is not None:
                if _pool:
                    _pool.release(conn)
                else:
                    conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")


def get_pool():
    """Returns the connection pool instance."""
    return _pool


def get_db():
    """FastAPI dependency that yields an oracledb connection."""
    conn = None
    try:
        if _pool:
            conn = _pool.acquire()
        else:
            conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=DSN)
        yield conn
    finally:
        try:
            if conn is not None:
                if _pool:
                    _pool.release(conn)
                else:
                    conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
