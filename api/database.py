import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    db_user = (os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "")).strip()
    db_pass = (os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "")).strip()
    db_host = (os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "")).strip()
    db_name = (os.getenv("POSTGRES_DATABASE") or os.getenv("DB_NAME", "postgres")).strip()
    db_port = "5432"

    if not all([db_user, db_pass, db_host]):
        return None

    try:
        return psycopg2.connect(
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
            sslmode='require',
            connect_timeout=20
        )
    except Exception:
        return None

def init_db():
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mercados (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                localizacao GEOGRAPHY(POINT, 4326),
                preco_cesta_total DECIMAL(10,2),
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mercados_localizacao ON mercados USING GIST(localizacao);")
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        if conn:
            conn.close()