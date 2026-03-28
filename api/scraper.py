import os
import requests
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        return psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME")
        )
    except Exception:
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
    except Exception:
        pass