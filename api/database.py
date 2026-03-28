import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME"),
            connect_timeout=10
        )
        return conn
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