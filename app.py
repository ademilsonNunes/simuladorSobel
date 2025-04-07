import streamlit as st
import pandas as pd
import plotly.express as px
import openai
import os
from dotenv import load_dotenv

# Carrega a chave da API do arquivo .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def gerar_relatorio_estrategico(prompt):
    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        return resposta['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {str(e)}")
        return None

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(page_title="Análise Comercial e Controladoria", layout="wide")
st.title("📊 One-Page Report Comercial & Controladoria")

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

# =============================
# UPLOAD DO ARQUIVO
# =============================
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
        redes = sorted(carteira_df["REDE"].unique()) if "REDE" in carteira_df.columns else []
        sups = sorted(carteira_df["SUP"].unique()) if "SUP" in carteira_df.columns else []
        vends = sorted(carteira_df["VENDEDOR"].unique()) if "VENDEDOR" in carteira_df.columns else []

        colf1, colf2, colf3, colf4, colf5, colf6 = st.columns(6)
        cliente_sel = colf1.selectbox("Filtrar Cliente", ["Todos"] + clientes)
        uf_sel = colf2.selectbox("Filtrar UF", ["Todos"] + ufs)
        sku_sel = colf3.selectbox("Filtrar Produto (SKU)", ["Todos"] + skus)
        rede_sel = colf4.selectbox("Filtrar Rede", ["Todos"] + redes) if redes else "Todos"
        sup_sel = colf5.selectbox("Filtrar Supervisor", ["Todos"] + sups) if sups else "Todos"
        vend_sel = colf6.selectbox("Filtrar Vendedor", ["Todos"] + vends) if vends else "Todos"

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
        if rede_sel != "Todos" and "REDE" in df_filtro.columns:
            df_filtro = df_filtro[df_filtro["REDE"] == rede_sel]
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
        # TABELA SIMPLIFICADA DE PREÇO E % LUCRO POR SKU
        # =============================
        st.markdown("---")
        st.subheader("📄 Faixa de Preço e Lucro por SKU")
        
        # Calculando os preços e % de lucro
        df_precos_aux = df_filtro.copy()
        df_precos_aux["PRECO_UNIT"] = df_precos_aux["VL.BRUTO"] / df_precos_aux["QTDE"]
        
        precos_resumo = df_precos_aux.groupby("SKU").agg({
            "PRECO_UNIT": ["min", "mean", "max"],
            "LUCRO LIQ": "sum",
            "VL.BRUTO": "sum",
            "QTDE": "sum"
        }).reset_index()
        
        precos_resumo.columns = [
            "SKU", "PREÇO MÍNIMO UNIT", "PREÇO MÉDIO UNIT", "PREÇO MÁXIMO UNIT",
            "LUCRO LIQ", "FATURAMENTO", "VOLUME"
        ]
        
        # Cálculo dos % Lucro
        precos_resumo["% LUCRO MIN"] = (precos_resumo["LUCRO LIQ"] / (precos_resumo["VOLUME"] * precos_resumo["PREÇO MÍNIMO UNIT"])) * 100
        precos_resumo["% LUCRO MÉDIO"] = (precos_resumo["LUCRO LIQ"] / (precos_resumo["VOLUME"] * precos_resumo["PREÇO MÉDIO UNIT"])) * 100
        precos_resumo["% LUCRO MAX"] = (precos_resumo["LUCRO LIQ"] / (precos_resumo["VOLUME"] * precos_resumo["PREÇO MÁXIMO UNIT"])) * 100
        
        # Formatação
        for col in ["PREÇO MÍNIMO UNIT", "PREÇO MÉDIO UNIT", "PREÇO MÁXIMO UNIT"]:
            precos_resumo[col] = precos_resumo[col].apply(formatar_moeda)
        
        for col in ["% LUCRO MIN", "% LUCRO MÉDIO", "% LUCRO MAX"]:
            precos_resumo[col] = precos_resumo[col].apply(lambda x: f"{x:.2f}%" if isinstance(x, float) else x)
        
        precos_resumo["VOLUME"] = precos_resumo["VOLUME"].astype(int)
        
        # Exibição
        st.dataframe(
            precos_resumo[["SKU", "PREÇO MÍNIMO UNIT", "% LUCRO MIN", "PREÇO MÉDIO UNIT", "% LUCRO MÉDIO", "PREÇO MÁXIMO UNIT", "% LUCRO MAX"]],
            use_container_width=True
        )
        # =============================
        # ANÁLISE DO PESO DO FRETE POR CLIENTE
        # =============================
        st.markdown("---")
        st.subheader("🚚 Peso do Frete sobre Faturamento por Cliente")
        
        # Verifica se existe coluna FRETE
        if "FRETE TOTAL" not in carteira_df.columns:
            st.warning("⚠️ A coluna 'FRETE TOTAL' não foi encontrada na base. Por favor, valide o arquivo de origem.")
        else:
            # Agrupamento
            df_frete = df_filtro.groupby("CLIENTE").agg({
                "VL.BRUTO": "sum",
                "FRETE TOTAL": "sum"
            }).reset_index()
        
            df_frete["% FRETE / FATURAMENTO"] = (df_frete["FRETE TOTAL"] / df_frete["VL.BRUTO"]) * 100
        
            # Formatação
            df_frete["VL.BRUTO"] = df_frete["VL.BRUTO"].apply(formatar_moeda)
            df_frete["FRETE TOTAL"] = df_frete["FRETE TOTAL"].apply(formatar_moeda)
            df_frete["% FRETE / FATURAMENTO"] = df_frete["% FRETE / FATURAMENTO"].apply(lambda x: f"{x:.2f}%")
        
            # Exibição Tabela
            st.dataframe(df_frete, use_container_width=True)
        
            # Gráfico de Barras
            st.subheader("📊 Percentual do Frete sobre Faturamento por Cliente")
        
            df_frete_grafico = df_filtro.groupby("CLIENTE").agg({
                "VL.BRUTO": "sum",
                "FRETE TOTAL": "sum"
            }).reset_index()
            df_frete_grafico["% FRETE / FATURAMENTO"] = (df_frete_grafico["FRETE TOTAL"] / df_frete_grafico["VL.BRUTO"]) * 100
        
            fig_frete = px.bar(
                df_frete_grafico.sort_values("% FRETE / FATURAMENTO", ascending=False),
                x="% FRETE / FATURAMENTO",
                y="CLIENTE",
                orientation="h",
                title="Peso do Frete sobre Faturamento por Cliente"
            )
            fig_frete.update_layout(xaxis_title="% Frete sobre Faturamento", yaxis_title="Cliente")
            fig_frete.update_traces(texttemplate="%{x:.2f}%", textposition="outside")
            st.plotly_chart(fig_frete, use_container_width=True)
        
            # =============================
            # GRÁFICO DE PIZZA CIF x FOB
            # =============================
            st.subheader("🥧 Distribuição CIF x FOB (por Volume Total de Caixas)")
        
            df_frete_pizza = carteira_df.groupby("TIPO_FRETE")["QTDE"].sum().reset_index()
            df_frete_pizza["COND. FRETE"] = df_frete_pizza["TIPO_FRETE"].map({"C": "CIF", "F": "FOB"})
            df_frete_pizza = df_frete_pizza[df_frete_pizza["QTDE"] > 0]
        
            fig_pizza = px.pie(
                df_frete_pizza,
                values="QTDE",
                names="COND. FRETE",
                title="Distribuição do Volume por Condição de Frete (CIF x FOB)"
            )
            fig_pizza.update_traces(textinfo="percent+label")
        
            st.plotly_chart(fig_pizza, use_container_width=True)
         
            # =============================
            # FUNÇÃO MELHORADA DE RELATÓRIO ESTRATÉGICO
            # =============================
            def gerar_relatorio_estrategico(dados):
                try:
                    # Agrupamentos para análise
                    def top_contribuintes(df, col, top_n=10):
                        dados = df.groupby(col).agg({
                            "VL.BRUTO": "sum",
                            "LUCRO LIQ": "sum"
                        }).reset_index()
                        dados["% LUCRO"] = (dados["LUCRO LIQ"] / dados["VL.BRUTO"]) * 100
                        dados = dados.sort_values("% LUCRO")
                        maiores = dados.tail(top_n).to_dict(orient="records")
                        menores = dados.head(top_n).to_dict(orient="records")
                        return maiores, menores
            
                    grupos = ["CLIENTE", "SKU", "REDE", "VENDEDOR"]
                    resumo_impacto = {}
                    for g in grupos:
                        if g in dados.columns:
                            maiores, menores = top_contribuintes(dados, g, top_n=10)
                            resumo_impacto[g] = {"maiores": maiores, "menores": menores}
            
                    resumo_exec = {
                        "Faturamento Total ": f"R$ {dados['VL.BRUTO'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        "Lucro Líquido Total ": f"R$ {dados['LUCRO LIQ'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                        "Margem Média ": f"{(dados['LUCRO LIQ'].sum() / dados['VL.BRUTO'].sum()) * 100:.2f}%",
                    }
            
                    prompt = f"""
                    Você é um analista de dados comerciais.
                    Com base nas informações abaixo, gere um relatório estratégico destacando:
            
                    ✅ Diagnóstico da Margem: quais clientes, produtos (SKUs), redes e vendedores aumentam ou reduzem a margem (% lucro)?
                    ✅ Apresente os **Top 10 que mais AUMENTAM** e os **Top 10 que mais REDUZEM** a margem para cada um dos grupos (cliente, produto, rede, vendedor).
                    ✅ Apresente um plano de ação com sugestões específicas por grupo para elevar a margem global.
            
                    Resumo Executivo:
                    {resumo_exec}
            
                    Impacto por Grupo:
                    {resumo_impacto}
            
                    Gere a resposta em linguagem clara e executiva.
                    """
            
                    resposta = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=2000
                    )
                    return resposta["choices"][0]["message"]["content"]
            
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {str(e)}")
                    return None
            
            # =============================
            # BLOCOS DE EXECUÇÃO (ajustado)
            # =============================
            if uploaded_file:
                with st.expander("📄 Análise Estratégica - AI insights"):
                    st.markdown("Relatório interpretativo com destaques dos principais fatores que impactam a margem.")
            
                    if st.button("📌 Gerar Diagnóstico"):
                        with st.spinner("Analisando impacto por Cliente, Produto, Rede e Vendedor..."):
                            relatorio = gerar_relatorio_estrategico(df_filtro)
                            if relatorio:
                                st.markdown("---")
                                st.markdown(relatorio)
                                st.success("✅ Diagnóstico gerado com sucesso!")
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
        - Rede

        Todos os cálculos, tabelas e gráficos respeitam os filtros aplicados na seção de **Filtros para Análise**.

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
        - Apresentar os percentuais sobre a base correspondente.

        Além disso, o relatório calcula:
        - **Total de Tributos Pagos** sobre cada base.
        - Percentual total da carga tributária.

        #### 4️⃣ **Importante**
        Os percentuais de tributos são calculados exclusivamente para análise gerencial, sem caráter de apuração oficial.

        Todos os resultados apresentados consideram o regime tributário de **Lucro Real**.

        ---

        ### 📄 **Resumo dos Cálculos**
        - **% Lucro = (Lucro Líquido / Faturamento) x 100**
        - **% Contrato = (Total Contrato / Faturamento) x 100**
        - **% Lucro Após Contrato = ((Lucro Líquido - Total Contrato) / Faturamento) x 100**
        - **Participação do Tributo = (Tributo / Base de Cálculo) x 100**

        Os filtros aplicados impactam diretamente em todos os indicadores e gráficos deste relatório.

        """)
        st.markdown("---")
        st.info("""
        Este relatório foi elaborado para fornecer uma visão executiva consolidada entre análise comercial e fiscal.
        A estrutura, lógica de cálculo e indicadores seguem boas práticas de mercado para empresas no regime de **Lucro Real**.
        Para projeções e simulações, recomenda-se utilizar módulos específicos.
        """)

