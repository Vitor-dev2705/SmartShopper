import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

try:
    from api.scraper import atualizar_area_automatica
except ImportError:
    try:
        from scraper import atualizar_area_automatica
    except ImportError:
        def atualizar_area_automatica(lat, lon): pass

load_dotenv()

app = FastAPI(title="SmartShopper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    try:
        return psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            connect_timeout=5
        )
    except Exception:
        return None

@app.get("/")
async def serve_index():
    base_path = Path(__file__).resolve().parent.parent
    index_path = base_path / "index.html"
    
    if index_path.exists():
        return FileResponse(str(index_path))
    
    local_path = Path(os.getcwd()) / "index.html"
    if local_path.exists():
        return FileResponse(str(local_path))
        
    return {"erro": f"index.html nao encontrado em {index_path}"}

@app.get("/v1/buscar-barato")
async def buscar_mais_barato(lat: float, lon: float, background_tasks: BackgroundTasks):
    background_tasks.add_task(atualizar_area_automatica, lat, lon)
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexao com banco")

    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
        SELECT 
            nome, 
            preco_cesta_total as preco, 
            ST_Distance(localizacao, ST_MakePoint(%s, %s)::geography) / 1000 as distancia_km,
            ST_Y(localizacao::geometry) as lat,
            ST_X(localizacao::geometry) as lon
        FROM mercados
        WHERE ST_DWithin(localizacao, ST_MakePoint(%s, %s)::geography, 15000)
        ORDER BY preco ASC, distancia_km ASC
        LIMIT 10;
        """
        cur.execute(query, (lon, lat, lon, lat))
        mercados = cur.fetchall()
        
        recomendacoes = []
        for m in mercados:
            recomendacoes.append({
                "nome": m['nome'],
                "preco": float(m['preco']),
                "distancia_km": round(float(m['distancia_km']), 2),
                "lat": float(m['lat']),
                "lon": float(m['lon'])
            })

        cur.close()
        conn.close()

        return {
            "status": "sucesso", 
            "recomendacoes": recomendacoes
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))