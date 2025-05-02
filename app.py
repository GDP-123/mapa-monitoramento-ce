import streamlit as st

from streamlit_folium import st_folium

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

# Interface da barra lateral
with st.sidebar:
    st.markdown("### 📰 Atualizações")
    notificacoes = buscar_notificacoes()
    for msg, data in notificacoes:
        st.markdown(f"**{data}** — {msg}")


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


# Título
cc1, cc2 = st.columns([1, 3])
with cc1:
    st.image("image\\logo.png", width=100)
with cc2:
    st.title("PAINEL DE LIDERANÇAS CRIMINOSAS - CEARÁ")

col111, col222, col333 = st.columns(3)
with col111:
    st.markdown("<h3 style='text-align:center'> Alvos catalogados</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>{len(df):,}</h2>", unsafe_allow_html=True)

with col222:
    st.markdown("<h3 style='text-align:center'> Com mandado em aberto</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>{df['possui_mandado'].sum():,}</h2>", unsafe_allow_html=True)

with col333:
    st.markdown("<h3 style='text-align:center'>Cidades mapeadas</h3>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center'>{df['cidade'].nunique()}</h2>", unsafe_allow_html=True)



# Layout com duas colunas: mapa à esquerda, dados à direita
col1, col2 = st.columns([1, 1])  # proporção 2:1

with col1:
    # Criar o mapa
    st.write("Use o controle no canto superior direito do mapa para mostrar/ocultar facções")
    m = folium.Map(location=[-5.2, -39.5], zoom_start=7)

    # Adicionar camada GeoJson
    geojson_layer = camada_amarela(ce_geo, m)
    
    # Adicionar coress das faccoes
    m = camada_colirada(dados,m,ce_geo)

    # Mostrar mapa e capturar clique
    mapa_data = st_folium(m, width=800, height=600, returned_objects=["last_object_clicked"])

with col2:
    try:
        if mapa_data and mapa_data.get("last_object_clicked"):
            #pegando as coordenadas do ponto clicado
            lat = mapa_data["last_object_clicked"]["lat"]
            lng = mapa_data["last_object_clicked"]["lng"]
            #localizando o lugar clicado
            clicked_city = encontrar_cidade_por_coordenada(lat, lng, ce_geo)

            if clicked_city:
                #pegando os dados da região clicada pelo usuário
                st.subheader(f"Membro(s) de ORCRIM em {clicked_city}")
                liderancas = df[df['cidade'].str.lower() == clicked_city.lower()]
                
                if not liderancas.empty:
                    # Criando um container com altura fixa e barra de rolagem
                    with st.container(height=585):  # Ajuste a altura conforme necessário
                        for _, dados in liderancas.iterrows():
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.image(dados.foto, width=280)
                            
                            with col2:
                                st.markdown(f"**Nome:** {dados.nome}")
                                st.markdown(f"**Facção:** {dados.faccao}")
                                st.markdown(f"**Cargo:** {dados.cargo}")
                                st.markdown(f"**Cidade:** {dados.cidade} ({dados.regiao})")
                                
                                if dados.possui_mandado:
                                    st.error(f"🚨 MP em aberto: {dados.quantidade_mandados}")
                                else:
                                    st.success("✅ Sem mandado em aberto")
                                
                                st.caption(f"🕒 Última atualização: {dados.ultima_atualizacao}")
                            
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
