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
root_dir = current_dir.parent

if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    import scraper
except ImportError:
    try:
        from . import scraper
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
    db_user = (os.getenv("POSTGRES_USER") or os.getenv("DB_USER", "")).strip()
    db_pass = (os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "")).strip()
    db_host = (os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST", "")).strip()
    db_name = (os.getenv("POSTGRES_DATABASE") or os.getenv("DB_NAME", "postgres")).strip()
    db_port = (os.getenv("DB_PORT") or "6543").strip()
    if not all([db_user, db_pass, db_host]):
        return None

    try:
        return psycopg2.connect(
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name,
            sslmode='require',
            connect_timeout=10
        )
    except Exception as e:
        try:
            return psycopg2.connect(
                user=db_user,
                password=db_pass,
                host=db_host,
                port="5432",
                database=db_name,
                sslmode='require',
                connect_timeout=10
            )
        except:
            raise e
    
@app.get("/")
async def serve_index():
    paths_to_try = [
        root_dir / "index.html",
        current_dir / "index.html",
        Path("/var/task/index.html"),
        Path(os.getcwd()) / "index.html"
    ]
    
    for path in paths_to_try:
        if path.exists():
            return FileResponse(str(path))
            
    return {"status": "erro", "mensagem": "index.html nao encontrado"}

@app.get("/v1/buscar-barato")
async def buscar_mais_barato(lat: float, lon: float, background_tasks: BackgroundTasks):
    if scraper and hasattr(scraper, 'atualizar_area_automatica'):
        try:
            background_tasks.add_task(scraper.atualizar_area_automatica, lat, lon)
        except:
            pass
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            nome, 
            preco_cesta_total as preco, 
            ST_Distance(localizacao, ST_MakePoint(%s, %s)::geography) / 1000 as distancia_km,
            ST_Y(localizacao::geometry) as lat,
            ST_X(localizacao::geometry) as lon
        FROM mercados
        WHERE ST_DWithin(localizacao, ST_MakePoint(%s, %s)::geography, 25000)
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

        return {"status": "sucesso", "recomendacoes": recomendacoes}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

@app.get("/debug-db")
async def debug_db():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return {"status": "Conexão com banco OK"}
    except Exception as err:
        return {
            "status": "Erro de Conexão",
            "detalhe_tecnico": str(err),
            "host_usado": os.getenv("DB_HOST"),
            "user_usado": os.getenv("DB_USER")
        }