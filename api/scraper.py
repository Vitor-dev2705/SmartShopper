import os
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
 
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL não encontrada.")
        return None

    try:
        conn = psycopg2.connect(db_url, sslmode='require', connect_timeout=20)
        return conn
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def atualizar_area_automatica(lat, lon):
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
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=30)
        data = response.json()

        conn = get_db_connection()
        if not conn:
            print("Falha ao conectar ao banco.")
            return

        cur = conn.cursor()

        for element in data.get('elements', []):
            nome = element.get('tags', {}).get('name', 'Supermercado Sem Nome')
            e_lat = element.get('lat') or element.get('center', {}).get('lat')
            e_lon = element.get('lon') or element.get('center', {}).get('lon')

            if e_lat and e_lon:
                cur.execute("""
                    INSERT INTO mercados (nome, localizacao, preco_cesta_total, ultima_atualizacao)
                    VALUES (%s, ST_MakePoint(%s, %s)::geography, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT DO NOTHING;
                """, (nome, e_lon, e_lat, 0.0))

        conn.commit()
        cur.close()
        conn.close()
        print("Dados atualizados com sucesso.")
    except Exception as e:
        print(f"Erro ao atualizar área automática: {e}")