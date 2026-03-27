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
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            connect_timeout=10
        )
    except Exception as e:
        return None

def salvar_preco_mercado(nome, preco, lat, lon):
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        query = """
        INSERT INTO mercados (nome, preco_cesta_total, localizacao)
        VALUES (%s, %s, ST_MakePoint(%s, %s)::geography)
        ON CONFLICT ON CONSTRAINT mercados_nome_localizacao_key 
        DO UPDATE SET preco_cesta_total = EXCLUDED.preco_cesta_total;
        """
        try:
            cur.execute(query, (nome, preco, lon, lat))
            conn.commit()
        except Exception as e:
            pass
        finally:
            cur.close()
            conn.close()