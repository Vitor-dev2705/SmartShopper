import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        return psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME"),
            connect_timeout=5
        )
    except Exception:
        return None

def salvar_preco_mercado(nome, preco, lat, lon):
    conn = get_db_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        query = """
        INSERT INTO mercados (nome, preco_cesta_total, localizacao)
        VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
        ON CONFLICT ON CONSTRAINT mercados_nome_localizacao_key 
        DO UPDATE SET 
            preco_cesta_total = EXCLUDED.preco_cesta_total,
            ultima_atualizacao = NOW();
        """
        cur.execute(query, (str(nome), float(preco), float(lon), float(lat)))
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()