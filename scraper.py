import requests
import random
from database import salvar_preco_mercado

def atualizar_area_automatica(lat, lon):
    raio = 4000 
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    overpass_query = f"""
    [out:json];
    (
      node["shop"~"supermarket|convenience|grocery"](around:{raio},{lat},{lon});
      way["shop"~"supermarket|convenience|grocery"](around:{raio},{lat},{lon});
    );
    out center;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=15)
        
        if response.status_code == 429:
            return

        dados = response.json()
        elementos = dados.get('elements', [])
        
        if not elementos:
            return

        for elemento in elementos:
            tags = elemento.get('tags', {})
            nome = tags.get('name') or tags.get('operator') or "Mercado Proximo"
            
            coords = elemento.get('center', elemento)
            lat_f = coords.get('lat')
            lon_f = coords.get('lon')

            preco_analisado = round(random.uniform(22.0, 50.0), 2)
            
            salvar_preco_mercado(nome, preco_analisado, lat_f, lon_f)
            
    except Exception as e:
        pass