import os
import psycopg2
from dotenv import load_dotenv

# Carrega variáveis do .env (local)
load_dotenv()

def get_db_connection():
 
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️ DATABASE_URL não encontrada.")
        return None

    try:
        conn = psycopg2.connect(db_url, sslmode='require', connect_timeout=20)
        return conn
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return None