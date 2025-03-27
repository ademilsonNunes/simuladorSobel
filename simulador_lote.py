import streamlit as st
import io
import pandas as pd
from scipy.optimize import fsolve

st.set_page_config(page_title="Simulador de preços Sobel", layout="wide")
st.title("📦 Simulador de Preço Negociado")

# Lista com produtos e dados fixos
produtos = [
    {"Descrição": "ÁGUA SANITÁRIA 5L", "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},
    {"Descrição": "ÁGUA SANITÁRIA 2L", "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},
    {"Descrição": "ÁGUA SANITÁRIA 1L", "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},     
    {"Descrição": "CLORO DE 5L / PRO", "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},
    {"Descrição": "CLORO DE 2,5L",     "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},  
    {"Descrição": "ALVEJANTE 1.5L",    "PREÇO SOBEL": 0.0, "MVA (%)": 56.86, "IPI (%)": 0.00},          
    {"Descrição": "AMACIANTE 5L",      "PREÇO SOBEL": 0.0, "MVA (%)": 42.24, "IPI (%)": 0.00},
    {"Descrição": "AMACIANTE 2L",      "PREÇO SOBEL": 0.0, "MVA (%)": 42.24, "IPI (%)": 0.00},        
    {"Descrição": "DESINF. 2L",         "PREÇO SOBEL": 0.0, "MVA (%)": 50.00, "IPI (%)": 5.00},
    {"Descrição": "DESINF. 2L CLORADO", "PREÇO SOBEL": 0.0, "MVA (%)": 50.00, "IPI (%)": 5.00},
    {"Descrição": "DESINF. 5L",         "PREÇO SOBEL": 0.0, "MVA (%)": 50.00, "IPI (%)": 5.00},           
    {"Descrição": "LAVA LOUÇAS 500ML", "PREÇO SOBEL": 0.0, "MVA (%)": 35.60, "IPI (%)": 3.25},
    {"Descrição": "LAVA LOUÇAS 5L",    "PREÇO SOBEL": 0.0, "MVA (%)": 35.60, "IPI (%)": 3.25},    
    {"Descrição": "LAVA ROUPAS 3L", "PREÇO SOBEL": 0.0, "MVA (%)": 32.08, "IPI (%)": 3.25},
    {"Descrição": "LAVA ROUPAS 1L", "PREÇO SOBEL": 0.0, "MVA (%)": 32.08, "IPI (%)": 3.25},        
    {"Descrição": "LIMPA VIDROS SQUEEZE 500ML", "PREÇO SOBEL": 0.0, "MVA (%)": 42.38, "IPI (%)": 3.25},    
    {"Descrição": "DESENGORDURANTE 500ML", "PREÇO SOBEL": 0.0, "MVA (%)": 42.38, "IPI (%)": 3.25},      
    {"Descrição": "MULTI-USO 500ML", "PREÇO SOBEL": 0.0, "MVA (%)": 42.38, "IPI (%)": 3.25},
    {"Descrição": "REMOVEDOR 1L", "PREÇO SOBEL": 0.0, "MVA (%)": 42.38, "IPI (%)": 3.25},
    {"Descrição": "REMOVEDOR 500ML", "PREÇO SOBEL": 0.0, "MVA (%)": 42.38, "IPI (%)": 3.25},
]

df_base = pd.DataFrame(produtos)

# ICMS Global
icms_percentual = st.sidebar.number_input("ICMS (%)", min_value=0.0, max_value=25.0, value=18.0, step=0.01)
icms = icms_percentual / 100

# Editor para preencher o PREÇO SOBEL
st.markdown("### ✍️ Informe os preços Sobel na tabela abaixo:")
df_editada = st.data_editor(df_base, use_container_width=True, num_rows="fixed")

# Cálculo do Preço Negociado por linha
def calcular_preco_sobel(preco_neg, mva, ipi, icms):
    ipi_valor = preco_neg * ipi
    base_st = preco_neg * (1 + ipi) * (1 + mva)
    st_valor = (base_st * icms) - (preco_neg * icms)
    return preco_neg + ipi_valor + st_valor

def encontrar_preco_negociado(preco_sobel, mva, ipi, icms):
    if preco_sobel <= 0:
        return 0.0
    f = lambda x: calcular_preco_sobel(x, mva, ipi, icms) - preco_sobel
    return round(fsolve(f, preco_sobel * 0.9)[0], 4)

# Prepara DataFrame para cálculo
df = df_editada.copy()
df["MVA DEC"] = df["MVA (%)"] / 100
df["IPI DEC"] = df["IPI (%)"] / 100

df["Preço Negociado"] = df.apply(
    lambda row: encontrar_preco_negociado(row["PREÇO SOBEL"], row["MVA DEC"], row["IPI DEC"], icms),
    axis=1
)

df["IPI Valor"] = df["Preço Negociado"] * df["IPI DEC"]
df["Base ST"] = df["Preço Negociado"] * (1 + df["IPI DEC"]) * (1 + df["MVA DEC"])
df["ST Valor"] = (df["Base ST"] * icms) - (df["Preço Negociado"] * icms)
df["Preço Sobel Simulado"] = df["Preço Negociado"] + df["IPI Valor"] + df["ST Valor"]
df["Diferença"] = df["Preço Sobel Simulado"] - df["PREÇO SOBEL"]

# Resultado
st.markdown("### 📊 Resultado do Cálculo")
st.dataframe(
    df[[ 
        "Descrição", "PREÇO SOBEL", "MVA (%)", "IPI (%)",
        "Preço Negociado", "IPI Valor", "ST Valor",
        "Preço Sobel Simulado", "Diferença"
    ]].style.format({
        "PREÇO SOBEL": "R$ {:.2f}",
        "Preço Negociado": "R$ {:.2f}",
        "IPI Valor": "R$ {:.2f}",
        "ST Valor": "R$ {:.2f}",
        "Preço Sobel Simulado": "R$ {:.2f}",
        "Diferença": "R$ {:.4f}"
    }),
    use_container_width=True
)

# Exportação para Excel
st.markdown("### 📥 Exportar para Excel")
df_exportar = df[[ 
    "Descrição", "PREÇO SOBEL", "MVA (%)", "IPI (%)",
    "Preço Negociado", "IPI Valor", "ST Valor",
    "Preço Sobel Simulado", "Diferença"
]]

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    df_exportar.to_excel(writer, index=False, sheet_name="Simulação")

st.download_button(
    label="📤 Baixar planilha Excel",
    data=buffer,
    file_name="simulacao_preco_negociado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

