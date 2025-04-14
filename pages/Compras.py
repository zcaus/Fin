import streamlit as st
import plotly.express as px
from utils import carregar_planilhas

st.set_page_config(
    page_title="Compras",
    page_icon="💰",
    layout="wide",
)

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)


col1, col2 ,col3, col4 = st.columns(4)

with col1:
        st.page_link("Inicio.py", label="Dashboard", icon="📊")
with col2:
        st.page_link("pages/Compras.py", label="Compras", icon="📇")
with col3:
        st.page_link("pages/Conta_Corrente.py", label="Conta Corrente", icon="💻")
with col4:
        st.page_link("pages/Relatorio_Vendas.py", label="Relatório de Vendas", icon="💳")


st.title("📦 Controle de Compras")
_, _, compras = carregar_planilhas()

abas_compras = list(compras.keys())
opcao = st.selectbox("Escolha uma aba da planilha de Compras:", abas_compras)
df = compras[opcao]

st.dataframe(df)

if "Status" in df.columns:
    fig = px.histogram(df, x="Status", color="Status", title="Situação das Compras")
    st.plotly_chart(fig, use_container_width=True)
