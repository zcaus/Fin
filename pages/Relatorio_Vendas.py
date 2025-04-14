import streamlit as st
import plotly.express as px
from utils import carregar_planilhas
import pandas as pd
import locale
from datetime import datetime

st.set_page_config(
    page_title="Relatório de Vendas",
    page_icon="📊",
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

st.title("📊 Relatório de Vendas")
relatorio, _, _ = carregar_planilhas()

# Obtém a lista de abas (supondo que elas sejam nomes de meses)
abas_relatorio = list(relatorio.keys())

# Cria uma lista com os nomes dos meses em minúsculo para comparação
meses = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", 
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

# Mapeia o mês atual para o nome correspondente
mes_atual = meses[datetime.now().month - 1]

# Procura o índice da aba que corresponda ao mês atual (comparação case insensitive)
default_index = 0  # fallback caso não encontre
for idx, aba in enumerate(abas_relatorio):
    if aba.lower() == mes_atual:
        default_index = idx
        break

# Cria o selectbox utilizando o índice padrão
opcao = st.selectbox("Mês", abas_relatorio, index=default_index)
df = relatorio[opcao]

# Verifica se é uma aba de mês (por ex. "Janeiro", "Fevereiro", "Março", etc.)
eh_mes = any(mes in opcao.lower() for mes in meses)

if eh_mes:
    # Converte as colunas numéricas (caso estejam como texto)
    df['META'] = pd.to_numeric(df['META'], errors='coerce')
    df['VENDAS 2025'] = pd.to_numeric(df['VENDAS 2025'], errors='coerce')

    # Cálculos agregados
    total_meta = df['META'].sum()
    total_vendas = df['VENDAS 2025'].sum()
    falta_meta = total_meta - total_vendas
    dias_passados = 31  # Março tem 31 dias, pode ser automatizado se necessário
    vendas_dia = total_vendas / dias_passados
    previsao_fechamento = df['PREVISÃO DE FECHAMENTO'].sum()  # manter proporcional à média

    # Layout de métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 META MENSAL", f"R$ {total_meta:,.2f}")
    col2.metric("💰 TOTAL VENDAS", f"R$ {total_vendas:,.2f}")
    col3.metric("📉 FALTA P/ META", f"R$ {falta_meta:,.2f}")
    col4.metric("📈 PREVISÃO FECHAMENTO", f"R$ {previsao_fechamento:,.2f}")

st.markdown("---")

col1, col2 = st.columns([1.4, 1])
with col1:
    # Gráfico comparativo entre 2025 e 2024
    comparativo = pd.DataFrame({
        'Ano': ['2024', '2025'],
        'Vendas': [df['VENDAS 2025'].sum(), df['VENDAS 2024'].sum()]
    })
    fig_comparativo = px.bar(comparativo, x='Ano', y='Vendas', text='Vendas',
                              title="📊 Comparativo de Vendas: 2024 x 2025",
                              labels={'Vendas': 'Total Vendido (R$)'})
    fig_comparativo.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
    st.plotly_chart(fig_comparativo, use_container_width=True)

with col2:
    colunas_para_mostrar = ['LOJA', 'VENDAS 2025', 'VENDAS 2024', 'META', 'PREVISÃO DE FECHAMENTO']
    df_visivel = df[colunas_para_mostrar]
    st.dataframe(df_visivel, use_container_width=True)

# Gráfico de barras (Meta x Venda Atual), se colunas existirem
if "META" in df.columns and "VENDAS 2025" in df.columns:
    fig = px.bar(df, x=df.columns[0], y=["META", "VENDAS 2025"], barmode="group",
                 title="📍 Meta vs Venda Atual por Loja")
    st.plotly_chart(fig, use_container_width=True)

# Relatório executivo: Lojas que bateram ou não bateram a meta
if eh_mes:
    df_relatorio = df.copy()

    # Garantir que as colunas estão como número
    df_relatorio['META'] = pd.to_numeric(df_relatorio['META'], errors='coerce')
    df_relatorio['VENDAS 2025'] = pd.to_numeric(df_relatorio['VENDAS 2025'], errors='coerce')

    st.markdown("### Performance por Loja")

col1, col2 = st.columns(2)
with col1:    # Lojas que bateram a meta
    lojas_ok = df_relatorio[df_relatorio['VENDAS 2025'] >= df_relatorio['META']]
    if not lojas_ok.empty:
        st.markdown("#### ✅ Lojas que bateram a meta:")
        for _, row in lojas_ok.iterrows():
            st.markdown(f"- 🟢 **{row['LOJA']}**: Vendeu R$ {row['VENDAS 2025']:,.2f} (Meta: R$ {row['META']:,.2f})")
    else:
        st.markdown("✅ Nenhuma loja bateu a meta.")

with col2:
    # Lojas que não bateram a meta
    lojas_nok = df_relatorio[df_relatorio['VENDAS 2025'] < df_relatorio['META']]
    if not lojas_nok.empty:
        st.markdown("#### ❌ Lojas que **não** bateram a meta:")
        for _, row in lojas_nok.iterrows():
            falta = row['META'] - row['VENDAS 2025']
            st.markdown(f"- 🔴 **{row['LOJA']}**: Vendeu R$ {row['VENDAS 2025']:,.2f} (Meta: R$ {row['META']:,.2f}) — **Faltou: R$ {falta:,.2f}**")
    else:
        st.markdown("🎉 Todas as lojas bateram a meta!")
