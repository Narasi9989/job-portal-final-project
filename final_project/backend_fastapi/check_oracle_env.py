import os
import traceback

print('ORACLE_HOME=', os.environ.get('ORACLE_HOME'))
print('PATH includes oracle=', any('oracle' in p.lower() for p in os.environ.get('PATH','').split(';')))
print('PATH sample=', os.environ.get('PATH','')[:500])
print('ORACLE_SID=', os.environ.get('ORACLE_SID'))
print('TNS_ADMIN=', os.environ.get('TNS_ADMIN'))
try:
    import oracledb
    print('oracledb version=', oracledb.__version__)
    print('has clientversion=', hasattr(oracledb, 'clientversion'))
    if hasattr(oracledb, 'clientversion'):
        try:
            print('clientversion=', oracledb.clientversion())
        except Exception as e:
            print('clientversion error', type(e).__name__, e)
    try:
        print('is_thin =', oracledb.thin)
    except Exception as e:
        print('thin check error', type(e).__name__, e)
except Exception:
    traceback.print_exc()
