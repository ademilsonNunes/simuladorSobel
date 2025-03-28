import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Simulador de Preço de Venda Sobel", layout="wide")
st.title("📊 Simulador de Formação de Preço de Venda")
st.image("Logo-Suprema-Slogan-Alta-ai-1.webp", width=300)

# Carga padrão de dados
arquivo_padrao = "Custo de reposição.xlsx"
if os.path.exists(arquivo_padrao):
    df_padrao = pd.read_excel(arquivo_padrao)
    df_padrao.columns = df_padrao.columns.str.strip()
else:
    st.warning("Arquivo padrão não encontrado. Por favor, envie a planilha manualmente.")
    df_padrao = pd.DataFrame()

# Sidebar
st.sidebar.header("Parâmetros Globais")
frete_padrao = st.sidebar.number_input("Frete por Caixa (R$)", min_value=0.0, value=1.50, step=0.01)
contrato_percentual = st.sidebar.number_input("% Contrato", min_value=0.0, max_value=100.0, value=1.00, step=0.01) / 100
ufs_disponiveis = df_padrao["UF"].dropna().unique().tolist() if not df_padrao.empty else []
uf_selecionado = st.sidebar.selectbox("Selecione a UF", options=ufs_disponiveis) if ufs_disponiveis else ""

# Upload Excel
uploaded_file = st.file_uploader("📂 Envie sua planilha atualizada (.xlsx)", type="xlsx")

if uploaded_file:
    df_base = pd.read_excel(uploaded_file)
    df_base.columns = df_base.columns.str.strip()
    df_base = df_base[df_base["UF"] == uf_selecionado].copy()
elif not df_padrao.empty:
    df_base = df_padrao[df_padrao["UF"] == uf_selecionado].copy()
else:
    st.stop()

# Filtro de produtos
produtos_esperados = [
    "ÁGUA SANITÁRIA 5L", "ÁGUA SANITÁRIA 2L", "ÁGUA SANITÁRIA 1L",
    "CLORO DE 5L / PRO", "CLORO DE 2,5L", "ALVEJANTE 1.5L",
    "AMACIANTE 5L", "AMACIANTE 2L",
    "DESINF. 2L", "DESINF. 2L CLORADO", "DESINF. 5L",
    "LAVA LOUÇAS 500ML", "LAVA LOUÇAS 5L",
    "LAVA ROUPAS 5L", "LAVA ROUPAS 3L", "LAVA ROUPAS 1L",
    "LIMPA VIDROS SQUEEZE 500ML", "DESENGORDURANTE 500ML",
    "MULTI-USO 500ML", "REMOVEDOR 1L", "REMOVEDOR 500ML"
]
df_base = df_base[df_base["Descrição"].isin(produtos_esperados)]

# Preenche valores ausentes
colunas_necessarias = ["Preço de Venda", "Quantidade", "Frete Caixa", "%Estrategico"]
for col in colunas_necessarias:
    if col not in df_base.columns:
        df_base[col] = 0.0 if "Preço" in col or "Frete" in col or "%" in col else 1

# Atualiza frete e contrato
df_base["Frete Caixa"] = frete_padrao
df_base["Contrato"] = contrato_percentual

# Reorganiza colunas
colunas = df_base.columns.tolist()
if "Preço de Venda" in colunas and "Quantidade" in colunas:
    colunas.insert(colunas.index("Preço de Venda") + 1, colunas.pop(colunas.index("Quantidade")))
df_base = df_base[colunas]

st.markdown("### ✏️ Edite os dados abaixo para simulação em lote")
df_editado = st.data_editor(df_base, use_container_width=True, num_rows="dynamic")

# Cálculo para cada linha
def calcular_linha(row):
    preco_venda = row["Preço de Venda"]
    qtd = row["Quantidade"]
    subtotal = preco_venda * qtd
    custo_total_unit = row["Custo NET"] + row["Custo Fixo"]

    despesas_percentuais = (
        row["ICMS"] + row["COFINS"] + row["PIS"] +
        row["Comissão"] + row["Bonificação"] +
        row["Contigência"] + row["Contrato"] + row["%Estrategico"]
    )
    despesas_reais = preco_venda * despesas_percentuais * qtd + (row["Frete Caixa"] * qtd)

    # Lucro
    lucro_bruto = (preco_venda - custo_total_unit) * qtd - despesas_reais
    lucro_liquido = lucro_bruto / 1.34 if lucro_bruto > 0 else lucro_bruto
    irpj = lucro_liquido * 0.25 if lucro_liquido > 0 else 0
    csll = lucro_liquido * 0.09 if lucro_liquido > 0 else 0
    receita_total = preco_venda * qtd
    lucro_percentual = (lucro_liquido / receita_total) * 100 if receita_total > 0 else 0

    return pd.Series({
        "Subtotal (R$)": subtotal,
        "Lucro Bruto (R$)": lucro_bruto,
        "Lucro Líquido (R$)": lucro_liquido,
        "IRPJ (R$)": irpj,
        "CSLL (R$)": csll,
        "Lucro %": lucro_percentual
    })

resultados = df_editado.apply(calcular_linha, axis=1)
resultado_final = pd.concat([df_editado, resultados], axis=1)

st.markdown("### 📊 Resultado da Simulação")
st.dataframe(resultado_final.style.format({
    "Custo NET": "R$ {:.2f}",
    "Custo Fixo": "R$ {:.2f}",
    "Preço de Venda": "R$ {:.2f}",
    "Frete Caixa": "R$ {:.2f}",
    "Subtotal (R$)": "R$ {:.2f}",
    "Lucro Bruto (R$)": "R$ {:.2f}",
    "Lucro Líquido (R$)": "R$ {:.2f}",
    "IRPJ (R$)": "R$ {:.2f}",
    "CSLL (R$)": "R$ {:.2f}",
    "Lucro %": "{:.2f}%"
}), use_container_width=True)

# Exportação para Excel
st.markdown("### 📄 Baixar resultado em Excel")
export_df = resultado_final.copy()
excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
    export_df.to_excel(writer, index=False, sheet_name="Resultado")
    writer.close()

st.download_button(
    label="📄 Baixar Excel com Resultado",
    data=excel_buffer.getvalue(),
    file_name="resultado_simulacao.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
