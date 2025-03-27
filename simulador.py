import streamlit as st
from scipy.optimize import fsolve

st.set_page_config(page_title="Simulador Tributário", layout="centered")
st.title("🧮 Simulador de Preço Negociado Sobel")

# 🔢 Base de produtos com suas MVA e IPI
produtos = {
    "ÁGUA DE 5L":        {"MVA": 56.86, "IPI": 0.00},
    "AMACIANTE 5L":      {"MVA": 42.24, "IPI": 0.00},
    "DESINFETANTE 2L":   {"MVA": 50.00, "IPI": 5.00},
    "LAVA LOUÇAS 500ML": {"MVA": 35.60, "IPI": 3.25},
    "LAVA ROUPAS 5L":    {"MVA": 32.08, "IPI": 3.25},
    "MULTI-USO 500ML":   {"MVA": 42.38, "IPI": 3.25},
    "REMOVEDOR 1L":      {"MVA": 42.38, "IPI": 3.25},
}

# 🎯 Seleção do produto
produto_selecionado = st.selectbox("Selecione o Produto", list(produtos.keys()))
dados_produto = produtos[produto_selecionado]

# Entrada do Preço Sobel
preco_sobel = st.number_input("Preço Sobel (com ST e IPI)", value=90.00, step=0.01)

# Fixar ICMS
icms = 0.18

# Usar MVA/IPI da tabela
mva = dados_produto["MVA"] / 100
ipi = dados_produto["IPI"] / 100

# Função de simulação com base na fórmula correta
def calcular_preco_sobel(preco_neg):
    ipi_valor = preco_neg * ipi
    base_st = preco_neg * (1 + ipi) * (1 + mva)
    st_valor = (base_st * icms) - (preco_neg * icms)
    return preco_neg + ipi_valor + st_valor

# Encontrar o preço negociado via fsolve
def encontrar_preco_negociado(sobel_dado):
    f = lambda x: calcular_preco_sobel(x) - sobel_dado
    preco_calc = fsolve(f, sobel_dado * 0.9)[0]
    return preco_calc

# Cálculo
preco_negociado = encontrar_preco_negociado(preco_sobel)
ipi_valor = preco_negociado * ipi
base_st = preco_negociado * (1 + ipi) * (1 + mva)
st_valor = (base_st * icms) - (preco_negociado * icms)
preco_sobel_simulado = preco_negociado + ipi_valor + st_valor

# Resultado
st.markdown("### Resultado")
st.write(f"**Preço Negociado:** R$ {preco_negociado:.2f}")
st.write(f"**IPI:** R$ {ipi_valor:.2f}")
st.write(f"**ST:** R$ {st_valor:.2f}")
st.write(f"**Preço Sobel Simulado:** R$ {preco_sobel_simulado:.2f}")
st.write(f"**Diferença:** R$ {preco_sobel_simulado - preco_sobel:.4f}")
