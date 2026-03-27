import time
from api.scraper import atualizar_area_automatica

PONTOS_INTERESSE = [
    {"nome": "Asa Sul", "lat": -15.8117, "lon": -47.8990},
    {"nome": "Asa Norte", "lat": -15.7634, "lon": -47.8711},
    {"nome": "Águas Claras", "lat": -15.8392, "lon": -48.0267},
    {"nome": "Taguatinga Centro", "lat": -15.8335, "lon": -48.0567},
    {"nome": "Ceilândia Centro", "lat": -15.8202, "lon": -48.1132},
    {"nome": "Guará II", "lat": -15.8258, "lon": -47.9819},
    {"nome": "Sudoeste", "lat": -15.7997, "lon": -47.9247}
]

def rodar_aquecimento():
    print("Iniciando aquecimento do banco de dados (SmartShopper DF)...")
    
    for ponto in PONTOS_INTERESSE:
        print(f"📍 Mapeando mercados em: {ponto['nome']}...")
        try:
            atualizar_area_automatica(ponto['lat'], ponto['lon'])
            print(f"{ponto['nome']} processado com sucesso.")
        except Exception as e:
            print(f"Erro em {ponto['nome']}: {e}")
        
        time.sleep(2)

    print("\n Aquecimento concluído! O banco está pronto para uso.")

if __name__ == "__main__":
    rodar_aquecimento()