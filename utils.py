import pandas as pd
import streamlit as st

@st.cache_data
def carregar_planilhas():
    relatorio = pd.read_excel("data/relatorio_vendas.xlsx", None)
    conta_corrente = pd.read_excel("data/conta_corrente.xlsx", None)
    compras = pd.read_excel("data/compras.xlsx", None)
    return relatorio, conta_corrente, compras
