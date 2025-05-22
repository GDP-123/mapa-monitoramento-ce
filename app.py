import streamlit as st
import io

from streamlit_folium import st_folium
from streamlit_image_viewer import image_viewer
from pathlib import Path

from functions import *

# INICIALIZAR DB
init_db()
# CARREGAR DADOS
df,dados, ce_geo = load_data()
# DEFINIR DIRETÓRIO BASE
base_dir = Path(__file__).parent
# DEFINIR FACÇÕES
cores_faccoes = {
        "Facção A": "red",
        "Facção B": "blue",
        "Facção C": "blue",
        "Facção D": "blue",
        "Facção E": "blue",
    }

# Reduzir margens com CSS
st.markdown(
    """
    <style>
    /* Ajusta a largura do conteúdo */
    .block-container {
        max-width: 92%;
    }
    """,
    unsafe_allow_html=True
)

# Interface da barra lateral
with st.sidebar:
    st.markdown("### 📰 Atualizações")
    notificacoes = buscar_notificacoes()
    for msg, data in notificacoes:
        st.markdown(f"**{data}** — {msg}")


# Título
cc1, cc2, cc3 = st.columns([1, 4, 1])
with cc1:
    #st.image("image\\logo.png", width=210)
    pass
with cc2:
    st.markdown("<h1 style='text-align:center'> PAINEL DE LIDERANÇAS CRIMINOSAS - CEARÁ</h1>", unsafe_allow_html=True)
    col111, col222, col333 = st.columns([1,2,1])
    with col111:
        st.markdown("<h3 style='text-align:center'> Alvos catalogados</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center'>{len(df):,}</h3>", unsafe_allow_html=True)

    with col222:
        st.markdown("<h3 style='text-align:center'> Com mandado em aberto</h3>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center'>{df['possui_mandado'].sum():,}</h3>", unsafe_allow_html=True)

    with col333:
        st.markdown("<h3 style='text-align:center'>Cidades mapeadas</h3>", unsafe_allow_html=True)
        #st.markdown(f"<h2 style='text-align:center'>{df['cidade'].nunique()}</h2>", unsafe_allow_html=True) -----------------AQUI
with cc3:
    #st.image("image\\logo.png", width=210)
    pass

# Layout com duas colunas: mapa à esquerda, dados à direita
col1, col2 = st.columns([1, 1]) 
with col1: #Mapa
    # Usar um form para agrupar os checkboxes
    with st.form("faccoes_form",border=False):
        cols = st.columns(len(cores_faccoes))
        faccoes_selecionadas = []
        
        for i, (faccao, cor) in enumerate(cores_faccoes.items()):
            with cols[i]:
                if st.checkbox(faccao, value=True, key=f"check_{faccao}"):
                    faccoes_selecionadas.append(faccao)
        
        # Botão para aplicar as seleções
        aplicado = st.form_submit_button("Aplicar Filtros")

    # Só atualiza o mapa quando o botão for clicado
    if aplicado:
        st.session_state.faccoes_selecionadas = faccoes_selecionadas

    # Criar o mapa
    m = folium.Map(location=[-5.2, -39.5], zoom_start=7)
    camada_amarela(ce_geo, m)
    m = poligonos_coloridos(cores_faccoes, dados, m, st.session_state.get('faccoes_selecionadas', list(cores_faccoes.keys())))
    mapa_data = st_folium(m, width=900, height=600, returned_objects=["last_object_clicked"])

with col2: #Informações
    try:
        if mapa_data and mapa_data.get("last_object_clicked"):
            #pegando as coordenadas do ponto clicado
            lat = mapa_data["last_object_clicked"]["lat"]
            lng = mapa_data["last_object_clicked"]["lng"]
            #localizando o lugar clicado
            clicked_city = encontrar_cidade_por_coordenada(lat, lng, ce_geo)

            if clicked_city:
                #Define qual cidade foi clicada
                liderancas = df[df['cidade'].apply(lambda c: contem_cidade(c, clicked_city))]
                
                #Cria cabeçalho
                col1111, col2222 = st.columns([2,0.4])
                with col1111:
                    st.markdown(f"<h2 style='text-align:center'> Membro(s) de ORCRIM em {clicked_city.title()}</h2><br>", unsafe_allow_html=True)

                #Botão para gerar relatório
                with col2222:
                    
                    #st.subheader("Gerar Relatório")       
                    if not liderancas.empty:
                        # listando as lideranaças da facção específica escolhida pelo usuário
                        liderancas_filtradas = liderancas[liderancas['faccao'].isin(st.session_state.faccoes_selecionadas)]
                        liderancas_filtradas = liderancas_filtradas.sort_values(by='nome')

                        docx = gerar_documento(
                            modelo_path='Modelo.docx',
                            regiao=clicked_city.title(),
                            dados_tabela=liderancas_filtradas
                        )

                        # 2. Salva o documento em um buffer
                        buffer = io.BytesIO()
                        docx.save(buffer)
                        buffer.seek(0)  # Importante: reposiciona o ponteiro para o início do arquivo
                        
                        # 3. Download no Streamlit
                        st.download_button(
                            label="📄 DOCX",
                            data=buffer,
                            file_name=f"relatorio_{clicked_city}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            icon=":material/download:",
                        )
                    else:
                        pass
                        #st.warning("Nenhum dado encontrado para gerar o relatório.")
                
            if not liderancas.empty:
                
                # listando as lideranaças da facção específica escolhida pelo usuário
                liderancas_filtradas = liderancas[liderancas['faccao'].isin(st.session_state.faccoes_selecionadas)]

                # Criando um container com altura fixa e barra de rolagem
                with st.container(height=605):  # Ajuste a altura conforme necessário

                    if liderancas_filtradas.empty:
                        st.warning("Nenhuma liderança encontrada para as facções selecionadas.")
                    else:
                        #ordernar em ordem alfabética
                        liderancas_filtradas = liderancas_filtradas.sort_values(by='nome')
                        
                        #mostrando os dados
                        for _, dados in liderancas_filtradas.iterrows():
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
                                
                            # Mostrar a mensagem se o botão de informações for pressionado
                            if st.session_state.get(f'show_msg_{dados.id}', False):
                                st.info(dados.analista_info)

                            # Mostrar a fonte da informação se o botão for pressionado
                            if st.session_state.get(f'show_fonte_{dados.id}', False):
                                st.info(dados.fonte)
                            
                            st.markdown("---")  # Separador entre registros
            
            else:
                st.info("Até o momento, nenhuma liderança cadastrada para esta cidade.")

    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Rodapé
st.write("---")

st.write("**Network URL**: http://10.10.9.182:8503 | **Usuário:** DIP | **Setor:** DEPARTAMENTO DE INTELIGÊNCIA POLICIAL")
