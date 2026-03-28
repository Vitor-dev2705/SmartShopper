import os
import psycopg2
import sys
from pathlib import Path
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    import scraper
except ImportError:
    try:
        from api import scraper
    except ImportError:
        scraper = None

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
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME"),
            connect_timeout=10
        )
    except Exception:
        return None

@app.get("/")
async def serve_index():
    paths_to_try = [
        current_dir.parent / "index.html",
        current_dir / "index.html",
        Path(os.getcwd()) / "index.html"
    ]
    
    for path in paths_to_try:
        if path.exists():
            return FileResponse(str(path))
            
    return {"erro": "index.html nao encontrado"}

@app.get("/v1/buscar-barato")
async def buscar_mais_barato(lat: float, lon: float, background_tasks: BackgroundTasks):
    if scraper and hasattr(scraper, 'atualizar_area_automatica'):
        try:
            background_tasks.add_task(scraper.atualizar_area_automatica, lat, lon)
        except:
            pass
    
    conn = get_db_connection()
    if not conn:
        return {"status": "erro", "recomendacoes": [], "mensagem": "Falha na conexao com o banco"}

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
        LIMIT 20;
        """
        cur.execute(query, (lon, lat, lon, lat))
        mercados = cur.fetchall()
        
        recomendacoes = []
        for m in mercados:
            recomendacoes.append({
                "nome": str(m['nome']),
                "preco": float(m['preco']) if m.get('preco') else 0.0,
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
        return {"status": "erro", "recomendacoes": [], "detalhe": str(e)}


@app.get("/debug-db")
async def debug_db():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return {"status": "Conexão com banco OK"}
        return {"status": "Erro", "detalhe": "Não foi possível conectar"}
    except Exception as e:
        return {"status": "Erro fatal", "detalhe": str(e)}