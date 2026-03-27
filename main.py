import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from scraper import atualizar_area_automatica 

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
            connect_timeout=10 
        )
    except Exception as e:
        return None

@app.get("/")
async def serve_index():
    if os.path.exists('index.html'):
        return FileResponse('index.html')
    return {"erro": "index.html nao encontrado"}

@app.get("/v1/buscar-barato")
async def buscar_mais_barato(lat: float, lon: float, background_tasks: BackgroundTasks):
    background_tasks.add_task(atualizar_area_automatica, lat, lon)
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Erro de conexao")

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
        ORDER BY preco_cesta_total ASC, distancia_km ASC
        LIMIT 10;
        """
        cur.execute(query, (lon, lat, lon, lat))
        mercados = cur.fetchall()
        cur.close()
        conn.close()

        return {
            "status": "sucesso", 
            "recomendacoes": mercados
        }
    except Exception as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)