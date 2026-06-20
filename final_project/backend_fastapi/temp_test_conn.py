import traceback
from database import DSN, _pool, get_connection

print('DSN=', DSN)
print('POOL=', _pool)
try:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('select 1 from dual')
        print('connected', cur.fetchone())
except Exception:
    traceback.print_exc()
