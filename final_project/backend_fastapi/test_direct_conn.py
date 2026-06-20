import traceback
from database import DSN, ORACLE_USER, ORACLE_PASSWORD, ORACLE_CLIENT_LIB_DIR
import oracledb

print('Client lib dir:', ORACLE_CLIENT_LIB_DIR)
print('DSN:', DSN)
print('User:', ORACLE_USER)

try:
    conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=DSN)
    print('Direct connection successful!')
    cur = conn.cursor()
    cur.execute('select 1 from dual')
    print('Query result:', cur.fetchone())
    conn.close()
except Exception as e:
    print(f'Direct connection failed: {type(e).__name__}: {e}')
    traceback.print_exc()
