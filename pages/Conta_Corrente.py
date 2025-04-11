import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import io

st.set_page_config(
    page_title="Conta Corrente",
    page_icon="💰",
    layout="wide",
)

BASE_DATA_DIR = "data"           # Pasta onde as planilhas estarão
BASE_IMAGE_DIR = "images"         # Pasta onde as imagens estarão (caso queira utilizá-las)
EXCEL_DADOS_FILE = os.path.join(BASE_DATA_DIR, "conta_corrente.xlsx")          # Arquivo Excel principal para o dashboard
EXCEL_CONTA_FILE = os.path.join(BASE_DATA_DIR, "conta_corrente.xlsx")          # Arquivo Excel com a Conta Corrente

def format_currency(value):
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

def load_data_from_excel_layout_vertical():
    if not os.path.exists(EXCEL_DADOS_FILE):
        st.error(f"O arquivo {EXCEL_DADOS_FILE} não foi encontrado!")
        return pd.DataFrame(columns=["Data", "Categoria", "Valor", "Tipo"])
    try:
        df_excel = pd.read_excel(EXCEL_DADOS_FILE, header=None)
        
        raw_periods = df_excel.iloc[1, 1:].tolist()
        
        month_map = {
            "JANEIRO": "01",
            "FEVEREIRO": "02",
            "MARÇO": "03",
            "ABRIL": "04",
            "MAIO": "05",
            "JUNHO": "06",
            "JULHO": "07",
            "AGOSTO": "08",
            "SETEMBRO": "09",
            "OUTUBRO": "10",
            "NOVEMBRO": "11",
            "DEZEMBRO": "12"
        }
        
        processed_periods = []
        for p in raw_periods:
            p_str = str(p).strip()
            if p_str.lower() == "nan" or p_str == "":
                processed_periods.append("")
            else:
                parts = p_str.split(".")
                if len(parts) == 2:
                    month_name = parts[0].strip().upper()
                    year = parts[1].strip()
                    month_num = month_map.get(month_name, "00")
                    period_standard = f"{year}-{month_num}"
                    processed_periods.append(period_standard)
                else:
                    processed_periods.append(p_str)
        
        period_index_pairs = [(i, p) for i, p in enumerate(processed_periods) if p != ""]
        period_index_pairs.sort(key=lambda x: x[1])
        sorted_indices = [i for i, p in period_index_pairs]
        sorted_periods = [p for i, p in period_index_pairs]
        
        data_values = df_excel.iloc[2:, 1:]
        data_values = data_values.iloc[:, sorted_indices]
        
        categories = df_excel.iloc[2:, 0].tolist()
        
        records = []
        for i, cat in enumerate(categories):
            category_str = str(cat).strip()
            if category_str.upper() in {"RECEITAS", "DESPESAS"}:
                continue
            for j, period in enumerate(sorted_periods):
                if period == "":
                    continue
                value = data_values.iloc[i, j]
                if pd.notnull(value):
                    valor = float(value)
                    if valor < 0:
                        tipo = "Despesa"
                        valor = abs(valor)
                    else:
                        tipo = "Receita"
                    records.append({
                        "Data": period,
                        "Categoria": category_str,
                        "Valor": valor,
                        "Tipo": tipo
                    })
        df_imported = pd.DataFrame(records)
        return df_imported

    except Exception as e:
        st.error("Erro ao carregar o arquivo Excel: " + str(e))
        return pd.DataFrame(columns=["Data", "Categoria", "Valor", "Tipo"])

def load_data_conta_corrente(sheet_name="MARÇO"):
    if not os.path.exists(EXCEL_CONTA_FILE):
        st.error(f"O arquivo {EXCEL_CONTA_FILE} não foi encontrado!")
        return pd.DataFrame()
    try:
        df = pd.read_excel(EXCEL_CONTA_FILE, sheet_name=sheet_name, header=None)
        df.columns = ["Descricao", "Valor"]

        def convert_to_float(valor):
            if pd.isna(valor):
                return None
            if isinstance(valor, (int, float)):
                return float(valor)
            valor = str(valor).strip()
            # Somente converte se estiver no formato monetário
            if not valor.startswith("R$"):
                return None
            valor = valor.replace("R$", "").strip()
            valor = valor.replace(".", "").replace(",", ".")
            try:
                return float(valor)
            except Exception:
                return None

        df["Valor"] = df["Valor"].apply(convert_to_float)
        return df

    except Exception as e:
        st.error("Erro ao ler os dados da Conta Corrente: " + str(e))
        return pd.DataFrame()

# Carregar os dados de layout vertical (caso você precise em outra parte)
data = load_data_from_excel_layout_vertical()

if "Categorias" not in st.session_state:
    st.session_state.Categorias = sorted(data["Categoria"].unique().tolist()) if not data.empty else []

st.title("📘 Conta Corrente")

# Lista de meses em português (em caixa alta e com acentuação, conforme suas abas no Excel)
meses = [
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"
]

# Obtém o mês atual como string (ex.: "MARÇO")
mes_atual = meses[datetime.now().month - 1]

if os.path.exists(EXCEL_CONTA_FILE):
    xls = pd.ExcelFile(EXCEL_CONTA_FILE)
    abas_conta = xls.sheet_names
    
    # Tenta definir a aba padrão para o mês atual
    if mes_atual in abas_conta:
        default_index = abas_conta.index(mes_atual)
    else:
        default_index = 0  # Fallback: usa a primeira aba se o mês atual não estiver presente
    
    opcao = st.selectbox("Mês:", abas_conta, index=default_index)
else:
    opcao = "MARÇO"  # Valor padrão se o arquivo não existir (apenas para não travar)

# Utiliza o sheet selecionado para carregar os dados
df = load_data_conta_corrente(sheet_name=opcao)
if df.empty:
    st.warning("Não há dados de Conta Corrente para exibir.")
else:
    df["Descricao"] = df["Descricao"].astype(str).str.upper().str.strip()

    faturamento_lojas = df.loc[df["Descricao"] == "FATURAMENTO LOJAS", "Valor"].values[0]
    faturamento_display = df.loc[df["Descricao"] == "FATURAMENTO DISPLAY/ATACADO", "Valor"].values[0]
    descontos = df.loc[df["Descricao"] == "DESCONTO LOJAS", "Valor"].values[0]
    perdas = df.loc[df["Descricao"] == "PERDAS LOJAS", "Valor"].values[0]
    resultado_faturamento = df.loc[df["Descricao"] == "RESULTADO DO FATURAMENTO", "Valor"].values[0]
    limite_compra_mes = df.loc[df["Descricao"] == "LIMITE COMPRA MÊS", "Valor"].values[0]
    saldo_disponivel = df.loc[df["Descricao"] == "SALDO DISPONIVEL PARA COMPRAS", "Valor"].values[0]

    faturamento_bruto = faturamento_lojas + faturamento_display
    resultado_faturamento_calculado = faturamento_bruto - descontos - perdas
    limite_calculado = resultado_faturamento_calculado * 0.40

    st.subheader("📊 Faturamento")
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Lojas", format_currency(faturamento_lojas))
    col2.metric("Faturamento Display", format_currency(faturamento_display))
    col3.metric("Faturamento Bruto", format_currency(faturamento_bruto))

    col4, col5, col6 = st.columns(3)
    col4.metric("Descontos", format_currency(descontos))
    col5.metric("Perdas", format_currency(perdas))
    col6.metric("Faturamento Líquido", format_currency(resultado_faturamento_calculado))
    
    st.markdown("---")

    st.subheader("🛒 Compras Realizadas")
            
    compras_para_aprovar = df.loc[df["Descricao"] == "COMPRAS PARA APROVAR (PENDENTE)", "Valor"].values[0]
    compras_em_transito = df.loc[df["Descricao"] == "COMPRAS EM TRÂNSITO", "Valor"].values[0]
    total_compras_nf = df.loc[df["Descricao"] == "TOTAL COMPRAS NOTA FISCAL", "Valor"].values[0]
    total_compras_nota_especial = df.loc[df["Descricao"] == "TOTAL COMPRAS NOTA ESPECIAL", "Valor"].values[0]
    total_compras_registradas = total_compras_nf + total_compras_nota_especial

    col1, col2, col3 = st.columns(3)
    col1.metric("Limite de Compra", format_currency(limite_calculado))
    col2.metric("Saldo Disponível", format_currency(saldo_disponivel))
    col3.metric("Nota Especial", format_currency(total_compras_nota_especial))

    colc1, colc2, colc3 = st.columns(3)
    colc1.metric("Compras P/ Aprovar", format_currency(compras_para_aprovar))
    colc2.metric("Compras em Trânsito", format_currency(compras_em_transito))
    colc3.metric("Compras NF", format_currency(total_compras_nf))

    st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    # Cria o gráfico de barras horizontal já existente
    fig = go.Figure(go.Bar(
        x=[resultado_faturamento_calculado, total_compras_registradas],
        y=["Faturamento", "Compras"],
        orientation='h',
        marker_color=['#244610', '#c3670d']
    ))

    # Adiciona a linha pontilhada no limite de compra
    fig.add_shape(
        type="line",
        x0=limite_calculado, x1=limite_calculado,  # Posição no eixo X (limite de compra)
        y0=0, y1=1,  # A linha cobre a totalidade do gráfico no eixo Y (referenciado em "paper")
        xref="x",
        yref="paper",
        line=dict(
            dash="dot",  # Linha pontilhada
            color="red",
            width=2
        )
    )

    fig.update_layout(
        xaxis_title="Valor (R$)",
        yaxis_title="Categoria",
        height=250,
        margin=dict(l=1, r=1, t=20, b=1)
    )
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("📊 Distribuição das Compras (%)")

    compras_dist = pd.DataFrame({
        "Categoria": ["P/ Aprovar", "Em Trânsito", "NF", "Nota Especial"],
        "Valor": [
            compras_para_aprovar, compras_em_transito,
            total_compras_nf, total_compras_nota_especial
        ]
    })

    fig_pizza = px.pie(
        compras_dist,
        names="Categoria",
        values="Valor",
        hole=0.5,
        color_discrete_sequence=["#1f77b4", "#c3670d", "#244610", "#d62728"],
    )

    fig_pizza.update_traces(textinfo='percent+label', textfont_size=12)
    fig_pizza.update_layout(
        title_text="",
        showlegend=False,
        height=250,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig_pizza, use_container_width=True)

st.markdown("---")
st.subheader("📋 Registros Detalhados")
st.dataframe(
    df.style.format({"Valor": "R$ {:,.2f}"} , thousands=".", decimal=","),
    use_container_width=True
)
