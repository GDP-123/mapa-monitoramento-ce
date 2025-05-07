import folium, json, sqlite3
import pandas as pd
import streamlit as st


from shapely.geometry import shape, Point
from collections import defaultdict
from folium import LayerControl
from folium.features import GeoJsonTooltip
from datetime import datetime

def camada_colorida(dados, m, ce_geo):
    # Cria o dicionário cidade -> lista de facções
    cidade_faccao = defaultdict(list)
    for pessoa in dados:
        # Agora pessoa['cidade'] é uma lista, então iteramos sobre cada cidade
        for cidade in pessoa['cidade']:
            faccao = pessoa['faccao']
            cidade_faccao[cidade].append(faccao)

    # Opcional: converter para dict comum se não quiser usar defaultdict
    cidade_faccao = dict(cidade_faccao)

    # Determinar a facção predominante em cada cidade
    faccao_predominante = {}
    for cidade, faccoes in cidade_faccao.items():
        # Contar ocorrências de cada facção
        contagem = {}
        for f in faccoes:
            contagem[f] = contagem.get(f, 0) + 1
        # Pegar a facção mais comum
        faccao_predominante[cidade] = max(contagem.items(), key=lambda x: x[1])[0]

    # Cores para cada facção (mantive suas cores originais)
    cores_faccoes = {
        "Facção A": "red",
        "Facção B": "blue",
        "Facção C": "green",
        "Facção D": "purple",
        "Facção E": "orange"
    }

    # Adicionar cada facção como uma camada separada
    for faccao, cor in cores_faccoes.items():
        # Filtrar cidades desta facção
        cidades_faccao = [
            feature for feature in ce_geo['features']
            if feature['properties']['name'] in faccao_predominante and 
            faccao_predominante[feature['properties']['name']] == faccao
        ]
        
        if not cidades_faccao:
            continue
        
        # Criar GeoJSON para esta facção
        geojson_faccao = {
            "type": "FeatureCollection",
            "features": cidades_faccao
        }
        
        # Adicionar ao mapa como camada
        folium.GeoJson(
            geojson_faccao,
            name=faccao,
            style_function=lambda x, cor=cor: {
                'fillColor': cor,
                'color': 'black',
                'weight': 0.5,
                'fillOpacity': 0.6
            },
            tooltip=GeoJsonTooltip(
                fields=['name'], 
                aliases=['Cidade:'],
                labels=True
            )
        ).add_to(m)

    # Adicionar controle de camadas
    folium.LayerControl().add_to(m)

    return m

def camada_amarela(ce_geo,m):
    geojson_layer = folium.GeoJson(
        ce_geo,
        name="Cidades",
        tooltip=folium.GeoJsonTooltip(fields=['name'], aliases=['Cidade:']),
        style_function=lambda x: {
            'fillColor': '#ffffff',
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.1,
        },
        highlight_function=lambda x: {
            'weight': 3,
            'color': 'yellow'
        },  # quando passar o mouse
    )
    geojson_layer.add_to(m)
    return geojson_layer

# Função para encontrar a cidade pelo ponto
def encontrar_cidade_por_coordenada(lat, lng, geojson):
    ponto = Point(lng, lat)  # Atenção: Point usa (x=lng, y=lat)
    
    for feature in geojson["features"]:
        poligono = shape(feature["geometry"])
        if poligono.contains(ponto):
            return feature["properties"]["name"]  # ou outro campo que quiser
    return None

# Função para mostrar/ocultar a mensagem
def toggle_mensagem():
    if 'mostrar_mensagem' not in st.session_state:
        st.session_state.mostrar_mensagem = False
    st.session_state.mostrar_mensagem = not st.session_state.mostrar_mensagem

@st.cache_data
def load_data():
    with open('dados.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    df = pd.DataFrame(dados)

    # Carregar GeoJSON
    with open('ce_cities.geojson', 'r', encoding='utf-8') as f:
        ce_geo = json.load(f)

    return df,dados,ce_geo

# Inicializa o banco de dados
def init_db():
    conn = sqlite3.connect('notificacoes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notificacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mensagem TEXT NOT NULL,
            data TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Adiciona uma notificação
def adicionar_notificacao(mensagem):
    conn = sqlite3.connect('notificacoes.db')
    c = conn.cursor()
    data_atual = datetime.now().strftime("%d/%m/%Y")
    c.execute('INSERT INTO notificacoes (mensagem, data) VALUES (?, ?)', (mensagem, data_atual))
    conn.commit()
    conn.close()

# Buscar notificacao
def buscar_notificacoes(limit=10):
    conn = sqlite3.connect('notificacoes.db')
    c = conn.cursor()
    c.execute('SELECT mensagem, data FROM notificacoes ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
