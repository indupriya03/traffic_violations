# db.py — works in BOTH notebook and Streamlit
import pandas as pd
from sqlalchemy import create_engine, text

# ===============================
# DETECT ENVIRONMENT
# ===============================
try:
    import streamlit as st
    IS_STREAMLIT = True
except ImportError:
    IS_STREAMLIT = False

# ===============================
# HELPER — error handler
# ===============================
def _handle_error(msg, e):
    if IS_STREAMLIT:
        st.error(f"{msg}: {e}")
    else:
        print(f"{msg}: {e}")

# ===============================
# DATABASE CONNECTION
# ===============================
def get_engine():
    return create_engine(
        "mysql+pymysql://root:root@localhost/traffic_violations",
        pool_pre_ping   = True,
        pool_size       = 10,       # ← increase pool size
        max_overflow    = 20,       # ← more connections
        pool_recycle    = 3600,     # ← recycle after 1hr
        pool_timeout    = 30,       # ← timeout after 30s
        echo            = False,
    )

if IS_STREAMLIT:
    get_engine = st.cache_resource(get_engine)

# ===============================
# QUERY RUNNER
# ===============================
def run_query(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn, params=params)
    except Exception as e:
        _handle_error("Query failed", e)
        return pd.DataFrame()

# ===============================
# WRITE RUNNER
# ===============================
def run_write(query, params=None):
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text(query), params or {})
            conn.commit()
            return True
    except Exception as e:
        _handle_error("Write failed", e)
        return False

# ===============================
# TEST CONNECTION
# ===============================
def test_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print("Connection successful! ✅")
        return True
    except Exception as e:
        _handle_error("Connection failed", e)
        return False
