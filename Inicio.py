import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import io

# ---------------------------
# Configurações Iniciais
# ---------------------------
st.set_page_config(
    page_title="Controle Financeiro",
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

# ---------------------------
# Constantes de Diretórios e Arquivos
# ---------------------------
BASE_DATA_DIR = "data"           # Pasta onde as planilhas estarão
BASE_IMAGE_DIR = "images"         # Pasta onde as imagens estarão (caso queira utilizá-las)
EXCEL_DADOS_FILE = os.path.join(BASE_DATA_DIR, "dados.xlsx")          # Arquivo Excel principal para o dashboard
EXCEL_CONTA_FILE = os.path.join(BASE_DATA_DIR, "conta_corrente.xlsx") # Arquivo Excel com a Conta Corrente

# ---------------------------
# Função Auxiliar para Formatação de Valores
# ---------------------------
def format_currency(value):
    """
    Formata um número float para o padrão monetário desejado:
    milhares separados por ponto e decimal separado por vírgula.
    Exemplo: 1234567.89 -> 'R$ 1.234.567,89'
    """
    formatted = f"{value:,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"

# ---------------------------
# Função para importar dados do Excel (Layout Vertical)
# ---------------------------
def load_data_from_excel_layout_vertical():
    """
    Lê o arquivo Excel (EXCEL_DADOS_FILE) com layout vertical.
    Espera que:
      - A célula A2 contenha "PERÍODO" e as células à direita (B2, C2, etc) contenham os períodos no formato "MÊS.ANO"
      - A partir da linha 3, a coluna A contém os nomes das categorias e as colunas seguintes possuem os valores para cada período.
    
    Retorna um DataFrame no formato longo com as colunas: Data, Categoria, Valor, Tipo.
    """
    if not os.path.exists(EXCEL_DADOS_FILE):
        st.error(f"O arquivo {EXCEL_DADOS_FILE} não foi encontrado!")
        return pd.DataFrame(columns=["Data", "Categoria", "Valor", "Tipo"])
    try:
        df_excel = pd.read_excel(EXCEL_DADOS_FILE, header=None)
        
        # Obtém os períodos (linha 2 – índice 1) a partir da coluna B em diante
        raw_periods = df_excel.iloc[1, 1:].tolist()
        
        # Mapeamento dos nomes dos meses em português para números
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
        
        # Processa os períodos para o formato "YYYY-MM"
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
        
        # Reordena os períodos cronologicamente
        period_index_pairs = [(i, p) for i, p in enumerate(processed_periods) if p != ""]
        period_index_pairs.sort(key=lambda x: x[1])
        sorted_indices = [i for i, p in period_index_pairs]
        sorted_periods = [p for i, p in period_index_pairs]
        
        # Seleciona os valores das transações a partir da linha 3
        data_values = df_excel.iloc[2:, 1:]
        data_values = data_values.iloc[:, sorted_indices]
        
        # Define as categorias a partir da coluna A (a partir da linha 3)
        categories = df_excel.iloc[2:, 0].tolist()
        
        records = []
        for i, cat in enumerate(categories):
            category_str = str(cat).strip()
            # Ignora as categorias que representam totais
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
                        "Data": period,  # Formato "YYYY-MM"
                        "Categoria": category_str,
                        "Valor": valor,
                        "Tipo": tipo
                    })
        df_imported = pd.DataFrame(records)
        return df_imported

    except Exception as e:
        st.error("Erro ao carregar o arquivo Excel: " + str(e))
        return pd.DataFrame(columns=["Data", "Categoria", "Valor", "Tipo"])

# ---------------------------
# Função para ler os dados da Conta Corrente
# ---------------------------
def load_data_conta_corrente(sheet_name="03.2025"):
    """
    Lê os dados da Conta Corrente do arquivo EXCEL_CONTA_FILE.
    
    O layout da planilha é exatamente o seguinte:

        CONTA CORRENTE MARÇO
        FATURAMENTO REALIZADO
        FATURAMENTO LOJAS          R$ 203.808,15 
        FATURAMENTO DISPLAY/ATACADO R$ 5.338,96 
        DESCONTO LOJAS             R$ 555,54 
        PERDAS LOJAS               R$ 567,14 
        RESULTADO DO FATURAMENTO   R$ 208.579,97 
        LIMITE COMPRA MÊS          R$ 83.658,84 
        COMPRA PARA ATACADO        R$ 2.000,00 
        SALDO DISPONIVEL PARA COMPRAS R$ 13.272,67 
        CUSTO FIXO GERAL (CD + LOJAS) R$ 152.000,00 
        DEVOLUÇÃO                
        TRANSFERENCIA PRODUTO ENTRE LOJAS R$ 77.820,62 
                
        COMPRAS REALIZADA ATÉ O MOMENTO
        COMPRAS PARA APROVAR (PENDENTE) R$ 465,00 
        COMPRAS EM TRÂNSITO          R$ 7.965,61 
        TOTAL COMPRAS NOTA FISCAL    R$ 52.300,52 
        TOTAL COMPRAS NOTA ESPECIAL  R$ 10.120,04 
        TOTAL RECEBIDAS GERAL        R$ 62.420,56 
        TOTAL RECEBIDAS + TRÂNSITO     R$ 70.386,17 

    Como há linhas de cabeçalho/grupo (que não possuem valor), a função converte apenas as células que
    apresentem string no formato monetário.
    
    Retorna um DataFrame com as colunas: [Descricao, Valor].
    """
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

# ----------------------------------------------------
# Carregamento dos Dados Principais (Layout Vertical)
# ----------------------------------------------------
data = load_data_from_excel_layout_vertical()

# Atualiza a lista de categorias no session_state a partir dos dados importados
if "Categorias" not in st.session_state:
    st.session_state.Categorias = sorted(data["Categoria"].unique().tolist()) if not data.empty else []


col1, col2 ,col3, col4 = st.columns(4)

with col1:
        st.page_link("Inicio.py", label="Dashboard", icon="📊")
with col2:
        st.page_link("pages/Compras.py", label="Compras", icon="📇")
with col3:
        st.page_link("pages/Conta_Corrente.py", label="Conta Corrente", icon="💻")
with col4:
        st.page_link("pages/Relatorio_Vendas.py", label="Relatório de Vendas", icon="💳")


# Cabeçalho do Dashboard
st.markdown(
    "<h1 style='text-align: center; color: #FFFFFF;'>Controle Financeiro</h1>",
    unsafe_allow_html=True
)

    # Filtro para o resumo do mês selecionado
col_filtro1, col_filtro2, col_filtro3, colfiltro4, colfiltro5, colfiltro6 = st.columns(6)
with col_filtro1:
        
        mes_atual = datetime.today().month
        ano_atual = datetime.today().year
        mes_anterior = mes_atual - 1 if mes_atual > 1 else 12
        ano_anterior = ano_atual if mes_atual > 1 else ano_atual - 1

        filtro_mes = st.selectbox(
            "Selecione o Mês",
            list(range(1, 13)),
            index=datetime.today().month - 1,
            key="resumo_mes"
        )

with col_filtro2:
        filtro_ano = st.number_input(
            "Selecione o Ano",
            min_value=2000,
            max_value=2100,
            value=datetime.today().year,
            step=1,
            key="resumo_ano"
        )
mes_ano_resumo = f"{int(filtro_ano)}-{int(filtro_mes):02d}"

    # Resumo do mês selecionado
st.header(f"📅 Resumo do Mês:")
filtro_data = data["Data"] == mes_ano_resumo
dados_filtrados = data[filtro_data]
receitas = dados_filtrados[dados_filtrados["Tipo"] == "Receita"]["Valor"].sum()
despesas = dados_filtrados[dados_filtrados["Tipo"] == "Despesa"]["Valor"].sum()
saldo = receitas - despesas

col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
with col_resumo1:
        st.metric(label="💸 Receitas", value=format_currency(receitas))
with col_resumo2:
        st.metric(label="🛒 Despesas", value=format_currency(despesas))
with col_resumo3:
        st.metric(label="⚖️ Saldo", value=format_currency(saldo))

if saldo > 0:
        st.success("🎉 Estamos em lucro nesse mês!")
elif saldo < 0:
        st.error("⚠️ Estamos em prejuízo nesse mês!")
else:
        st.info("🔄 O saldo deste mês está equilibrado.")

    # Gráfico Comparativo Mensal (Receita vs Despesa)
col1, col2 = st.columns(2)
with col1:
        st.header("Comparativo Mensal")
        if not data.empty:
            resumo = data.groupby(["Data", "Tipo"])["Valor"].sum().reset_index()
            resumo = resumo.rename(columns={"Data": "AnoMes"})
            resumo["AnoMes_dt"] = pd.to_datetime(resumo["AnoMes"], format="%Y-%m", errors="coerce")
            selected_year = filtro_ano
            selected_month = filtro_mes

            months_to_show = []
            if selected_month > 1:
                months_to_show.append(selected_month - 2)
            if selected_month > 1:
                months_to_show.append(selected_month - 1)
            months_to_show.append(selected_month)
            if selected_month < 12:
                months_to_show.append(selected_month + 1)
            if selected_month < 12:
                months_to_show.append(selected_month + 2)

            resumo_filtered = resumo[
                (resumo["AnoMes_dt"].dt.year == selected_year) &
                (resumo["AnoMes_dt"].dt.month.isin(months_to_show))
            ]
            
            fig = px.bar(
                resumo_filtered,
                x="AnoMes",
                y="Valor",
                color="Tipo",
                title="Comparativo Receita vs Despesa Mensal",
                labels={"Valor": "Valor (R$)", "AnoMes": "Mês"},
                barmode="group",
                color_discrete_map={"Receita": "#244610", "Despesa": "#c3670d"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠ Nenhuma transação registrada para gerar o gráfico.")
with col2:
        st.header("Despesas por Categoria")
        dados_despesas = dados_filtrados[dados_filtrados["Tipo"] == "Despesa"]
        dados_despesas = dados_despesas[~dados_despesas["Categoria"].isin(["Faturamento - Spezia", "Faturamento - AMD"])]
        if not dados_despesas.empty:
            fig_pizza = px.pie(dados_despesas, names="Categoria", values="Valor", title="Distribuição das Despesas")
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.warning("Nenhuma despesa registrada para o período selecionado.")

st.markdown("---")
    # Gráfico Comparativo de Lucro/Prejuízo entre Anos
st.markdown(
    "<h2 style='text-align: center; color: #FFFFFF;'>Comparativo Geral</h2>",
    unsafe_allow_html=True
)
    
if not data.empty:
        data["Lucro"] = data.apply(lambda row: row["Valor"] if row["Tipo"] == "Receita" else -row["Valor"], axis=1)
        data["Data_dt"] = pd.to_datetime(data["Data"], format="%Y-%m", errors="coerce")
        data = data.dropna(subset=["Data_dt"])
        data["Ano"] = data["Data_dt"].dt.year
        data["Mes"] = data["Data_dt"].dt.month
        
        df_result = data.groupby(["Ano", "Mes"])["Lucro"].sum().reset_index()
        month_map_pt = {
            1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
            5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
            9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
        }
        df_result["MesNome"] = df_result["Mes"].map(month_map_pt)
        
        anos_disponiveis = sorted(df_result["Ano"].unique())
        anos_selecionados = st.multiselect("Selecione os anos para comparar", 
                                           anos_disponiveis, default=anos_disponiveis)
        
        df_compare = df_result[df_result["Ano"].isin(anos_selecionados)]
        df_compare = df_compare.sort_values(by="Mes")
        
        fig_lucro = px.bar(
        df_compare,
        x="MesNome",
        y="Lucro",
        color="Ano",
        barmode="group",
        title="Comparativo Mensal de Lucro/Prejuízo entre Anos",
        labels={"Lucro": "Lucro/Prejuízo (R$)", "MesNome": "Mês"},

    )
        st.plotly_chart(fig_lucro, use_container_width=True)
else:
        st.warning("⚠️ Nenhuma transação registrada para gerar o gráfico de lucro/prejuízo.")

    # Registros Detalhados com Filtros por Categoria e Mês
st.markdown(
    "<h2 style='text-align: center; color: #FFFFFF;'>📋 Registros Detalhados</h2>",
    unsafe_allow_html=True
)
col_reg1, col_reg2 = st.columns(2)
with col_reg1:
        filtro_categoria = st.selectbox("Filtrar por Categoria", ["Todos"] + st.session_state.Categorias, key="filtro_categoria")
with col_reg2:
        meses_disponiveis = sorted(data["Data"].unique()) if not data.empty else []
        filtro_mes_reg = st.selectbox("Filtrar por Mês", ["Todos"] + meses_disponiveis, key="filtro_mes_reg")
    
data_filtrada = data.copy()
if filtro_categoria != "Todos":
        data_filtrada = data_filtrada[data_filtrada["Categoria"] == filtro_categoria]
if filtro_mes_reg != "Todos":
        data_filtrada = data_filtrada[data_filtrada["Data"] == filtro_mes_reg]
    
data_filtrada_view = data_filtrada.drop(columns=["Lucro", "Data_dt", "Ano", "Mes"], errors="ignore")
    
if not data_filtrada_view.empty:
        st.dataframe(
            data_filtrada_view.style.format(
                {"Valor": "R$ {:,.2f}"},
                thousands=".",
                decimal=","
            ),
            use_container_width=True
        )
else:
        st.warning("⚠️ Nenhuma transação encontrada com os filtros aplicados.")
    
    # Exportação de Dados
st.header("📤 Exportar Dados")
if not data.empty:
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            csv = data.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name="financas.csv",
                mime="text/csv",
            )
        with col_exp2:
            buffer = io.BytesIO()
            data.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="📥 Baixar Excel",
                data=buffer,
                file_name="financas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
else:
        st.warning("⚠ Nenhuma transação registrada para exportar.")