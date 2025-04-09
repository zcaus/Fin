import streamlit as st
import plotly.express as px
from utils import carregar_planilhas

st.title("📦 Controle de Compras")
_, _, compras = carregar_planilhas()

abas_compras = list(compras.keys())
opcao = st.selectbox("Escolha uma aba da planilha de Compras:", abas_compras)
df = compras[opcao]

st.dataframe(df)

if "Status" in df.columns:
    fig = px.histogram(df, x="Status", color="Status", title="Situação das Compras")
    st.plotly_chart(fig, use_container_width=True)
