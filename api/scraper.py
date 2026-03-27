import requests
import random
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    from database import salvar_preco_mercado
except ImportError:
    try:
        from api.database import salvar_preco_mercado
    except ImportError:
        def salvar_preco_mercado(*args): pass

def atualizar_area_automatica(lat, lon):
    raio = 3000 
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    overpass_query = f"""
    [out:json][timeout:10];
    (
      nwr["shop"~"supermarket|convenience|grocery|wholesale|market"](around:{raio},{lat},{lon});
      nwr["amenity"~"market"](around:{raio},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=8)
        
        if response.status_code != 200:
            return

        dados = response.json()
        elementos = dados.get('elements', [])
        
        if not elementos:
            return

        for elemento in elementos:
            tags = elemento.get('tags', {})
            
            nome = tags.get('name') or tags.get('brand') or tags.get('operator') or "Mercado Proximo"
            
            coords = elemento.get('center', elemento)
            
            lat_f = round(float(coords.get('lat')), 5)
            lon_f = round(float(coords.get('lon')), 5)

            if lat_f and lon_f:
                
                preco_analisado = round(random.uniform(25.0, 75.0), 2)
                salvar_preco_mercado(nome, preco_analisado, lat_f, lon_f)
            
    except Exception:
        pass