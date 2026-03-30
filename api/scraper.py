import os
import requests
import psycopg2
import socket
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (local)
load_dotenv()

def get_db_connection():
    """
    Estabelece conexão com o banco resolvendo o host para IPv4.
    Isso evita falhas de conexão 'Cannot assign requested address' em ambientes locais.
    """
    # Captura variáveis de ambiente (prioriza integração Vercel, depois .env)
    db_user = (os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "")).strip()
    db_pass = (os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "")).strip()
    db_host = (os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "")).strip()
    db_name = (os.getenv("POSTGRES_DATABASE") or os.getenv("DB_NAME", "postgres")).strip()
    db_port = "5432"

    if not all([db_user, db_pass, db_host]):
        print("⚠️ Variáveis de ambiente incompletas.")
        return None

    try:
        # Força resolução para IPv4
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

def atualizar_area_automatica(lat, lon):
    """
    Consulta a API Overpass para encontrar supermercados num raio de 5km
    e insere no banco de dados com localização geográfica (PostGIS).
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["shop"="supermarket"](around:5000, {lat}, {lon});
      way["shop"="supermarket"](around:5000, {lat}, {lon});
    );
    out center;
    """

    try:
        # Busca dados do OpenStreetMap
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=30)
        data = response.json()

        conn = get_db_connection()
        if not conn:
            print("⚠️ Falha ao conectar ao banco.")
            return

        cur = conn.cursor()

        for element in data.get('elements', []):
            nome = element.get('tags', {}).get('name', 'Supermercado Sem Nome')
            e_lat = element.get('lat') or element.get('center', {}).get('lat')
            e_lon = element.get('lon') or element.get('center', {}).get('lon')

            if e_lat and e_lon:
                # Insere usando ST_MakePoint para o tipo GEOGRAPHY do PostGIS
                cur.execute("""
                    INSERT INTO mercados (nome, localizacao, preco_cesta_total, ultima_atualizacao)
                    VALUES (%s, ST_MakePoint(%s, %s)::geography, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT DO NOTHING;
                """, (nome, e_lon, e_lat, 0.0))

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Dados atualizados com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao atualizar área automática: {e}")