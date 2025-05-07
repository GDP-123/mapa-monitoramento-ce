import streamlit as st

from streamlit_folium import st_folium
from streamlit_image_viewer import image_viewer
from pathlib import Path

from functions import *


# Reduzir margens com CSS
st.markdown(
    """
    <style>
    /* Ajusta a largura do conteúdo */
    .block-container {
        max-width: 92%;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# Carregar dados
df,dados, ce_geo = load_data()
# Inicializa DB
init_db()

#definindo diretório base
base_dir = Path(__file__).parent

# Interface da barra lateral
with st.sidebar:
    st.markdown("### 📰 Atualizações")
    notificacoes = buscar_notificacoes()
    for msg, data in notificacoes:
        st.markdown(f"**{data}** — {msg}")


# Título
cc1, cc2 = st.columns([1, 3])
with cc1:
    #st.image("image\\logo.png", width=100)
    pass
with cc2:
    st.title("PAINEL DE LIDERANÇAS CRIMINOSAS - CEARÁ")

# Exemplo: inserir notificações manualmente para testes
#with st.expander("Adicionar nova notificação"):
#    nova_msg = st.text_area("Mensagem da notificação")
#    if st.button("Adicionar"):
#        if nova_msg.strip():
#            adicionar_notificacao(nova_msg.strip())
#            st.success("Notificação adicionada!")
#            st.experimental_user()
#        else:
#            st.error("A mensagem não pode estar vazia.")

col111, col222, col333 = st.columns(3)
with col111:
    st.markdown("<h3 style='text-align:center'> Alvos catalogados</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>{len(df):,}</h2>", unsafe_allow_html=True)

with col222:
    st.markdown("<h3 style='text-align:center'> Com mandado em aberto</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>{df['possui_mandado'].sum():,}</h2>", unsafe_allow_html=True)

with col333:
    st.markdown("<h3 style='text-align:center'>Cidades mapeadas</h3>", unsafe_allow_html=True)
    #st.markdown(f"<h2 style='text-align:center'>{df['cidade'].nunique()}</h2>", unsafe_allow_html=True) -----------------AQUI



# Layout com duas colunas: mapa à esquerda, dados à direita
col1, col2 = st.columns([1, 1])  # proporção 2:1

with col1: #Mapa
    # Criar o mapa
    st.write("Use o controle no canto superior direito do mapa para mostrar/ocultar facções")
    m = folium.Map(location=[-5.2, -39.5], zoom_start=7)

    # Adicionar camada GeoJson
    geojson_layer = camada_amarela(ce_geo, m)
    
    # Adicionar coress das faccoes
    #m = camada_colirada(dados,m,ce_geo) -----------------AQUI
    m = camada_colorida(dados,m,ce_geo)

    # Mostrar mapa e capturar clique
    mapa_data = st_folium(m, width=800, height=600, returned_objects=["last_object_clicked"])

with col2: #Informações
    try:
        if mapa_data and mapa_data.get("last_object_clicked"):
            #pegando as coordenadas do ponto clicado
            lat = mapa_data["last_object_clicked"]["lat"]
            lng = mapa_data["last_object_clicked"]["lng"]
            #localizando o lugar clicado
            clicked_city = encontrar_cidade_por_coordenada(lat, lng, ce_geo)

            if clicked_city:
                #pegando os dados da região clicada pelo usuário
                #st.subheader(f"Membro(s) de ORCRIM em {clicked_city}")
                #liderancas = df[df['cidade'].str.lower() == clicked_city.lower()]
                if clicked_city:
                    st.subheader(f"Membro(s) de ORCRIM em {clicked_city.title()}")
                    
                    # Função de filtro segura
                    def contem_cidade(cidades_lista, cidade_alvo):
                        if not isinstance(cidades_lista, list):  # Caso algum valor não seja lista
                            return False
                        return any(cidade_alvo.lower() == c.lower() for c in cidades_lista)
                    
                    liderancas = df[df['cidade'].apply(
                        lambda c: contem_cidade(c, clicked_city)
                    )]
                
                
                if not liderancas.empty:
                    # Criando um container com altura fixa e barra de rolagem
                    with st.container(height=585):  # Ajuste a altura conforme necessário
                        for _, dados in liderancas.iterrows():
                            col1, col2, col3 = st.columns([1, 2, 0.2])
                            
                            with col1: #Foto
                                foto_path = base_dir / dados.foto  # dados.foto = "imagem/anonymous.jpg"
                                st.image(foto_path, width=280)
                                st.caption(f"🕒 Última atualização: {dados.ultima_atualizacao}")

                            with col2: #Dados
                                st.markdown(f"**Nome:** {dados.nome}")
                                st.markdown(f"**Facção:** {dados.faccao}")
                                st.markdown(f"**Cargo:** {dados.cargo}")
                                cidades = ', '.join(sorted(dados.cidade)) if dados.cidade else "Sem registro"
                                st.markdown(f"**Cidade:** {cidades}")
                                st.markdown(f"**Status:** {dados.status}")
                                
                                if dados.possui_mandado:
                                    st.error(f"🚨 MP em aberto: {dados.quantidade_mandados}")
                                else:
                                    st.success("✅ Sem mandado em aberto")
                                
                            with col3: #Botões
                                # Botão com chave única baseada no dados.id
                                if st.button("⚠️", 
                                        key=f"btn_{dados.id}",  # Chave única baseada no ID
                                        help="Clique para ver informações do analista"):
                                    # Inicializa ou alterna o estado específico para este ID
                                    if f'show_msg_{dados.id}' not in st.session_state:
                                        st.session_state[f'show_msg_{dados.id}'] = False
                                    st.session_state[f'show_msg_{dados.id}'] = not st.session_state[f'show_msg_{dados.id}']
                                if st.button("📄", 
                                            key=f"btn_info_{dados.id}",
                                            help="Clique para ver fonte da informação"):
                                    # Alterna o estado específico para este ID
                                    st.session_state[f'show_fonte_{dados.id}'] = not st.session_state.get(f'show_fonte_{dados.id}', False)
                                    # Garante que o analista não seja mostrado
                                    st.session_state[f'show_analista_{dados.id}'] = False
                                
                            # Mostrar a mensagem se o estado for True
                            if st.session_state.get(f'show_msg_{dados.id}', False):
                                st.info(dados.analista_info)

                            # Mostrar a fonte da informação se o estado for True
                            if st.session_state.get(f'show_fonte_{dados.id}', False):
                                st.info(dados.fonte)
                            
                            st.markdown("---")  # Separador entre registros
                
                else:
                    st.info("Até o momento, nenhuma liderança cadastrada para esta cidade.")
            else:
                st.warning("Clique dentro de uma cidade válida.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Rodapé
st.write("---")
st.write("**Network URL**: http://10.10.9.182:8503 | **Usuário:** DIP | **Setor:** DEPARTAMENTO DE INTELIGÊNCIA POLICIAL")
