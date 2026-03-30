import os
import psycopg2
import socket
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carrega variáveis do .env (local)
load_dotenv()

def get_db_connection():
    # Captura e limpa as variáveis de ambiente
    db_user = (os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "")).strip()
    db_pass = (os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "")).strip()
    db_host = (os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "")).strip()
    db_name = (os.getenv("POSTGRES_DATABASE") or os.getenv("DB_NAME", "postgres")).strip()
    db_port = "5432"

    # Validação básica para evitar tentativas com campos vazios
    if not all([db_user, db_pass, db_host]):
        print("⚠️ Variáveis de ambiente incompletas.")
        return None

    try:
        # Força resolução para IPv4 (evita erro 'Cannot assign requested address' no IPv6)
        ipv4_host = socket.gethostbyname(db_host)

        conn = psycopg2.connect(
            user=db_user,
            password=db_pass,
            host=ipv4_host,
            port=db_port,
            database=db_name,
            sslmode='require',
            connect_timeout=20
        )
        return conn
    except Exception as e:
        print(f"❌ Erro de conexão com IPv4: {e}")
        # Fallback: tenta com o host original
        try:
            conn = psycopg2.connect(
                user=db_user,
                password=db_pass,
                host=db_host,
                port=db_port,
                database=db_name,
                sslmode='require',
                connect_timeout=20
            )
            return conn
        except Exception as final_err:
            print(f"❌ Erro crítico de conexão: {final_err}")
            return None