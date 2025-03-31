import streamlit as st
import pandas as pd
import plotly.express as px

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(page_title="Análise Comercial e Fiscal", layout="wide")
st.title("📊 One-Page Report Comercial & Fiscal")

st.markdown("#### 1️⃣ Upload e Validação dos Dados")
st.markdown("Envie o arquivo Excel com as abas **CARTEIRA** e **Mark-up** para análise.")

# =============================
# FUNÇÕES UTILITÁRIAS
# =============================

def carregar_dados(caminho_arquivo):
    try:
        excel_data = pd.ExcelFile(caminho_arquivo)
        if {"CARTEIRA", "Mark-up"}.issubset(excel_data.sheet_names):
            carteira_df = excel_data.parse("CARTEIRA")
            markup_df = excel_data.parse("Mark-up")
            carteira_df.columns = carteira_df.columns.str.strip().str.upper()
            markup_df.columns = markup_df.columns.str.strip().str.upper()
            return carteira_df, markup_df
        else:
            st.error("O arquivo deve conter as abas 'CARTEIRA' e 'Mark-up'.")
            return None, None
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {str(e)}")
        return None, None

# =============================
# FORMATADORES
# =============================
formatar_moeda = lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
formatar_valor = lambda x: f"{x:,.0f}".replace(",", ".")

def highlight_negative(row):
    if "% LUCRO" in row:
        lucro = float(row["% LUCRO"].replace("%", "").replace(",", "."))
    else:
        lucro = float(row["% LUCRO TOTAL"].replace("%", "").replace(",", "."))
    return ["background-color: #ffb3b3" if lucro < 0 else "" for _ in row]

uploaded_file = st.file_uploader("📂 Escolha o arquivo Excel", type=["xlsx"])
if uploaded_file:
    carteira_df, markup_df = carregar_dados(uploaded_file)

    if carteira_df is not None:
        st.success("✅ Arquivo carregado com sucesso!")

        # =============================
        # FILTROS
        # =============================
        st.markdown("---")
        st.header("🎯 Filtros para Análise")

        clientes = sorted(carteira_df["CLIENTE"].unique())
        ufs = sorted(carteira_df["UF"].unique())
        skus = sorted(carteira_df["SKU"].unique())
        sups = sorted(carteira_df["SUP"].unique()) if "SUP" in carteira_df.columns else []
        vends = sorted(carteira_df["VENDEDOR"].unique()) if "VENDEDOR" in carteira_df.columns else []

        colf1, colf2, colf3, colf4, colf5 = st.columns(5)
        cliente_sel = colf1.selectbox("Filtrar Cliente", ["Todos"] + clientes)
        uf_sel = colf2.selectbox("Filtrar UF", ["Todos"] + ufs)
        sku_sel = colf3.selectbox("Filtrar Produto (SKU)", ["Todos"] + skus)
        sup_sel = colf4.selectbox("Filtrar Supervisor", ["Todos"] + sups) if sups else "Todos"
        vend_sel = colf5.selectbox("Filtrar Vendedor", ["Todos"] + vends) if vends else "Todos"

        # =============================
        # APLICAÇÃO DOS FILTROS
        # =============================
        df_filtro = carteira_df.copy()
        if cliente_sel != "Todos":
            df_filtro = df_filtro[df_filtro["CLIENTE"] == cliente_sel]
        if uf_sel != "Todos":
            df_filtro = df_filtro[df_filtro["UF"] == uf_sel]
        if sku_sel != "Todos":
            df_filtro = df_filtro[df_filtro["SKU"] == sku_sel]
        if sup_sel != "Todos" and "SUP" in df_filtro.columns:
            df_filtro = df_filtro[df_filtro["SUP"] == sup_sel]
        if vend_sel != "Todos" and "VENDEDOR" in df_filtro.columns:
            df_filtro = df_filtro[df_filtro["VENDEDOR"] == vend_sel]

        # =============================
        # PAINEL RESUMO
        # =============================
        st.markdown("---")
        st.header("📌 Painel Resumo")

        total_volume = int(df_filtro["QTDE"].sum())
        faturamento = df_filtro["VL.BRUTO"].sum()
        lucro_liq = df_filtro["LUCRO LIQ"].sum()
        preco_medio = faturamento / total_volume if total_volume > 0 else 0
        perc_lucro = (lucro_liq / faturamento) * 100 if faturamento > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Faturamento (R$)", formatar_moeda(faturamento))
        col2.metric("Volume Total (unid)", formatar_valor(total_volume))
        col3.metric("Preço Médio (R$)", formatar_moeda(preco_medio))
        col4.metric("Lucro Líquido (R$)", f"{formatar_moeda(lucro_liq)} ({perc_lucro:.2f}%)")
        # =============================
        # ANÁLISE DE LUCRO POR CLIENTE
        # =============================
        st.markdown("---")
        st.subheader("📄 Lucro por Cliente")

        lucro_cliente = df_filtro.groupby("CLIENTE")[["VL.BRUTO", "LUCRO LIQ"]].sum().reset_index()
        lucro_cliente["% LUCRO"] = (lucro_cliente["LUCRO LIQ"] / lucro_cliente["VL.BRUTO"]) * 100
        lucro_cliente["VL.BRUTO"] = lucro_cliente["VL.BRUTO"].apply(formatar_moeda)
        lucro_cliente["LUCRO LIQ"] = lucro_cliente["LUCRO LIQ"].apply(formatar_moeda)
        lucro_cliente["% LUCRO"] = lucro_cliente["% LUCRO"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            lucro_cliente.style.apply(
                lambda row: ["background-color: #ffb3b3" if float(row["% LUCRO"].replace("%", "").replace(",", ".")) < 0 else "" for _ in row],
                axis=1
            ),
            use_container_width=True
        )

        # =============================
        # ANÁLISE DE LUCRO POR SKU
        # =============================
        st.subheader("📄 Lucro por Produto (SKU)")

        lucro_sku = df_filtro.groupby("SKU")[["VL.BRUTO", "LUCRO LIQ"]].sum().reset_index()
        lucro_sku["% LUCRO"] = (lucro_sku["LUCRO LIQ"] / lucro_sku["VL.BRUTO"]) * 100
        lucro_sku["VL.BRUTO"] = lucro_sku["VL.BRUTO"].apply(formatar_moeda)
        lucro_sku["LUCRO LIQ"] = lucro_sku["LUCRO LIQ"].apply(formatar_moeda)
        lucro_sku["% LUCRO"] = lucro_sku["% LUCRO"].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            lucro_sku.style.apply(
                lambda row: ["background-color: #ffb3b3" if float(row["% LUCRO"].replace("%", "").replace(",", ".")) < 0 else "" for _ in row],
                axis=1
            ),
            use_container_width=True
        )

        # =============================
        # GRÁFICOS DE LUCRO POR SKU
        # =============================
        st.markdown("---")
        st.subheader("📊 Lucro Líquido por Produto (SKU) - Valor (R$)")

        lucro_prod = df_filtro.groupby("SKU")["LUCRO LIQ"].sum().reset_index().sort_values(by="LUCRO LIQ", ascending=False)
        fig_valor = px.bar(lucro_prod, x="LUCRO LIQ", y="SKU", orientation="h", title="Lucro Líquido Total por SKU")
        st.plotly_chart(fig_valor, use_container_width=True)

        st.subheader("📊 Lucro Líquido por Produto (SKU) - Percentual (%)")

        lucro_pct = df_filtro.groupby("SKU").agg({"LUCRO LIQ": "sum", "VL.BRUTO": "sum"}).reset_index()
        lucro_pct["% LUCRO"] = (lucro_pct["LUCRO LIQ"] / lucro_pct["VL.BRUTO"]) * 100

        fig_pct = px.bar(lucro_pct, x="% LUCRO", y="SKU", orientation="h", title="Percentual de Lucro Líquido por SKU")
        fig_pct.update_layout(xaxis_tickformat=".2f")
        st.plotly_chart(fig_pct, use_container_width=True)
        # =============================
        # TABELA DETALHADA DE PREÇO UNITÁRIO E LUCRO
        # =============================
        st.markdown("---")
        st.subheader("📄 Preço Unitário e Lucro por SKU - Análise Detalhada")

        df_precos_aux = df_filtro.copy()
        df_precos_aux["PRECO_UNIT"] = df_precos_aux["VL.BRUTO"] / df_precos_aux["QTDE"]

        precos_resumo = df_precos_aux.groupby("SKU").agg({
            "PRECO_UNIT": ["mean", "min", "max"],
            "LUCRO LIQ": "sum",
            "VL.BRUTO": "sum",
            "QTDE": "sum"
        }).reset_index()

        precos_resumo.columns = [
            "SKU", "PREÇO MÉDIO UNIT", "PREÇO MÍNIMO UNIT", "PREÇO MÁXIMO UNIT",
            "LUCRO LIQ", "FATURAMENTO", "VOLUME"
        ]

        precos_resumo["LUCRO UNIT"] = precos_resumo["LUCRO LIQ"] / precos_resumo["VOLUME"]
        precos_resumo["% LUCRO TOTAL"] = (precos_resumo["LUCRO LIQ"] / precos_resumo["FATURAMENTO"]) * 100
        precos_resumo["% LUCRO MIN"] = (precos_resumo["LUCRO UNIT"] / precos_resumo["PREÇO MÍNIMO UNIT"]) * 100
        precos_resumo["% LUCRO MAX"] = (precos_resumo["LUCRO UNIT"] / precos_resumo["PREÇO MÁXIMO UNIT"]) * 100
        precos_resumo["% LUCRO MÉDIO"] = (precos_resumo["LUCRO UNIT"] / precos_resumo["PREÇO MÉDIO UNIT"]) * 100

        # Formatação
        for col in ["PREÇO MÉDIO UNIT", "PREÇO MÍNIMO UNIT", "PREÇO MÁXIMO UNIT", "LUCRO LIQ", "FATURAMENTO", "LUCRO UNIT"]:
            precos_resumo[col] = precos_resumo[col].apply(formatar_moeda)

        for col in ["% LUCRO TOTAL", "% LUCRO MIN", "% LUCRO MAX", "% LUCRO MÉDIO"]:
            precos_resumo[col] = precos_resumo[col].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)

        precos_resumo["VOLUME"] = precos_resumo["VOLUME"].astype(int)

        st.dataframe(precos_resumo.style.apply(highlight_negative, axis=1), use_container_width=True)

        # =============================
        # PESO DO CONTRATO POR CLIENTE
        # =============================
        st.markdown("---")
        st.subheader("📄 Peso do Contrato por Cliente")

        df_contrato = df_filtro.groupby("CLIENTE").agg({
            "VL.BRUTO": "sum",
            "TOTAL CONTRATO": "sum",
            "LUCRO LIQ": "sum"
        }).reset_index()

        df_contrato["% CONTRATO"] = (df_contrato["TOTAL CONTRATO"] / df_contrato["VL.BRUTO"]) * 100
        df_contrato["% LUCRO ANTES CONTRATO"] = (df_contrato["LUCRO LIQ"] / df_contrato["VL.BRUTO"]) * 100
        df_contrato["% LUCRO APÓS CONTRATO"] = ((df_contrato["LUCRO LIQ"] - df_contrato["TOTAL CONTRATO"]) / df_contrato["VL.BRUTO"]) * 100

        # Formatação
        df_contrato["VL.BRUTO"] = df_contrato["VL.BRUTO"].apply(formatar_moeda)
        df_contrato["TOTAL CONTRATO"] = df_contrato["TOTAL CONTRATO"].apply(formatar_moeda)
        df_contrato["LUCRO LIQ"] = df_contrato["LUCRO LIQ"].apply(formatar_moeda)
        df_contrato["% CONTRATO"] = df_contrato["% CONTRATO"].apply(lambda x: f"{x:.2f}%")
        df_contrato["% LUCRO ANTES CONTRATO"] = df_contrato["% LUCRO ANTES CONTRATO"].apply(lambda x: f"{x:.2f}%")
        df_contrato["% LUCRO APÓS CONTRATO"] = df_contrato["% LUCRO APÓS CONTRATO"].apply(lambda x: f"{x:.2f}%")

        # Função para destacar linhas negativas
        def highlight_contrato(row):
            lucro = float(row["% LUCRO APÓS CONTRATO"].replace("%", "").replace(",", "."))
            return ["background-color: #ffb3b3" if lucro < 0 else "" for _ in row]

        # Exibir tabela
        st.dataframe(df_contrato.style.apply(highlight_contrato, axis=1), use_container_width=True)

        # =============================
        # DASHBOARD FISCAL AJUSTADO
        # =============================
        st.markdown("---")
        st.header("🧾 Dashboard Fiscal")
        
        # Mapeamento correto das colunas
        tributos = {
            "ICMS": "TOTAL ICMS",
            "ICMS-ST": "ICMS_ST",
            "PIS": "TOTAL PIS",
            "COFINS": "TOTAL COFINS",
            "IPI": "TOTAL IPI",
            "IRPJ": "IRPJ",
            "CSLL": "CSLL"
        }
        
        valores = {}
        for tributo, col in tributos.items():
            valores[tributo] = carteira_df[col].sum() if col in carteira_df.columns else 0
        
        faturamento_total = carteira_df["VL.BRUTO"].sum()
        lucro_liq_total = carteira_df["LUCRO LIQ"].sum()
        
        # Separação dos tributos sobre faturamento e sobre lucro
        tributos_faturamento = ["ICMS", "ICMS-ST", "PIS", "COFINS", "IPI"]
        tributos_lucro = ["IRPJ", "CSLL"]
        
        dados_tabela = []
        total_tributos = 0
        total_tributos_faturamento = 0
        total_tributos_lucro = 0
        
        for tributo in tributos:
            valor = valores[tributo]
            if tributo in tributos_faturamento:
                perc = (valor / faturamento_total) * 100 if faturamento_total > 0 else 0
                total_tributos_faturamento += valor
            else:
                if lucro_liq_total > 0:
                    perc = (valor / lucro_liq_total) * 100
                    total_tributos_lucro += valor
                else:
                    perc = 0  # Não considera IRPJ e CSLL se lucro ≤ 0
                    valor = 0
            total_tributos += valor
            dados_tabela.append([tributo, valor, perc])
        
        # Criando DataFrame para exibição
        df_fiscal = pd.DataFrame(dados_tabela, columns=["Tributo", "Valor (R$)", "% Base Referência"])
        df_fiscal["Valor (R$)"] = df_fiscal["Valor (R$)"].apply(formatar_moeda)
        df_fiscal["% Base Referência"] = df_fiscal["% Base Referência"].apply(lambda x: f"{x:.2f}%")
        
        # Exibição
        st.subheader("📄 Resumo dos Tributos")
        st.dataframe(df_fiscal, use_container_width=True)
        
        # Exibição dos Totalizadores
        colt1, colt2, colt3 = st.columns(3)
        colt1.metric("Total Tributos Faturamento (R$)", formatar_moeda(total_tributos_faturamento))
        colt2.metric("Total Tributos sobre Lucro (R$)", formatar_moeda(total_tributos_lucro if lucro_liq_total > 0 else 0))
        colt3.metric("Total Geral Tributos (R$)", formatar_moeda(total_tributos))
        # =============================
        # GRÁFICO DA CARGA TRIBUTÁRIA
        # =============================
        
        st.markdown("---")
        st.subheader("📊 Carga Tributária sobre Faturamento e Lucro")
        
        # Prepara dados para gráfico
        dados_grafico = []
        for tributo, col in tributos.items():
            valor = valores[tributo]
            if tributo in tributos_faturamento:
                perc = (valor / faturamento_total) * 100 if faturamento_total > 0 else 0
                base = "Faturamento Bruto"
            else:
                if lucro_liq_total > 0:
                    perc = (valor / lucro_liq_total) * 100
                    base = "Lucro Líquido"
                else:
                    perc = 0
                    valor = 0
                    base = "Lucro Líquido"
            dados_grafico.append([tributo, valor, perc, base])
        
        df_grafico = pd.DataFrame(dados_grafico, columns=["Tributo", "Valor (R$)", "% Base", "Base"])
        
        # Remove tributos zerados
        df_grafico = df_grafico[df_grafico["Valor (R$)"] > 0]
        
        # Gráfico de barras
        fig = px.bar(
            df_grafico,
            x="% Base",
            y="Tributo",
            color="Base",
            text="% Base",
            orientation="h",
            title="Participação dos Tributos nas Bases de Cálculo"
        )
        
        fig.update_layout(xaxis_title="% Base", yaxis_title="Tributo")
        fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        
        st.plotly_chart(fig, use_container_width=True)

        # =============================
        # NOTA EXPLICATIVA E METODOLOGIA DE CÁLCULO
        # =============================
        
        st.markdown("---")
        st.header("ℹ️ Nota Explicativa e Metodologia de Cálculo")
        
        st.markdown("""
        ### 🟢 Metodologia Aplicada
        
        #### 1️⃣ **Análise Comercial**
        O relatório consolida informações de faturamento, volume, preço médio e lucro líquido com base nos dados da aba **CARTEIRA**, considerando os seguintes filtros:
        - Cliente
        - UF (Estado)
        - Produto (SKU)
        - Supervisor
        - Vendedor
        
        O cálculo da margem de lucro considera o resultado líquido da venda (descontados contratos, comissões, despesas e tributos).
        
        #### 2️⃣ **Análise de Lucro**
        O relatório apresenta:
        - **Lucro por Cliente**
        - **Lucro por Produto (SKU)**
        - **Análise Detalhada do Preço Unitário e Lucro por SKU**
          - Preço Unitário Médio, Mínimo e Máximo
          - % de Lucro sobre cada um destes preços
          - Lucro Unitário por SKU
        - **Peso do Contrato por Cliente**
          - Percentual do valor do contrato sobre o faturamento
          - Impacto do contrato na margem de lucro
          - As linhas com % Lucro Negativo estão destacadas em vermelho
        
        #### 3️⃣ **Análise Fiscal**
        A análise fiscal considera os tributos destacados na nota fiscal:
        - ICMS
        - ICMS-ST (destaque separado, não compõe lucro)
        - PIS
        - COFINS
        - IPI
        - IRPJ (sobre Lucro Líquido)
        - CSLL (sobre Lucro Líquido)
        
        ##### Critérios:
        - A **Participação dos Tributos no Faturamento Bruto** considera:
            - ICMS, ICMS-ST, PIS, COFINS, IPI.
        - A **Participação dos Tributos sobre o Lucro Líquido** considera:
            - IRPJ e CSLL somente se o lucro líquido for positivo.
        
        O gráfico fiscal foi ajustado para:
        - Separar a base de cálculo (Faturamento Bruto ou Lucro Líquido).
        - Remover tributos zerados ou não aplicáveis no período.
        
        Além disso, o relatório calcula:
        - **Total de Tributos Pagos** sobre cada base.
        - Percentual total da carga tributária.
        
        #### 4️⃣ **Importante**
        Os percentuais de tributos são calculados exclusivamente para análise gerencial, sem caráter de apuração oficial.
        
        ---
        
        ### 📄 **Resumo dos Cálculos**
        - **% Lucro = (Lucro Líquido / Faturamento) x 100**
        - **% Contrato = (Total Contrato / Faturamento) x 100**
        - **% Lucro Após Contrato = ((Lucro Líquido - Total Contrato) / Faturamento) x 100**
        - **Participação do Tributo = (Tributo / Base de Cálculo) x 100**
        
        """)
        
        st.markdown("---")
        st.info("""
        Este relatório foi elaborado para oferecer uma visão executiva integrada entre Análise Comercial e Fiscal.
        A estrutura, cálculos e indicadores seguem boas práticas de gestão de resultados no regime de **Lucro Real**.
        Para projeções, simulações ou cenários, utilize módulos específicos a serem disponibilizados.
        """)

