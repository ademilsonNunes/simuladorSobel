Simulador de Formação de Preço de Venda - Sobel Suprema
Este simulador foi desenvolvido para apoiar a área comercial e financeira na correta formação do preço de venda, considerando todos os componentes de custo, despesas, impostos e margens estratégicas, de acordo com as regras fiscais vigentes.

🚀 Objetivo
Permitir que os gestores realizem simulações e ajustes na composição do preço de venda, de forma prática, transparente e técnica, possibilitando a análise do impacto de cada variável na margem e no resultado final.

📌 Lógica de Cálculo Utilizada
1. Subtotal
Calculado multiplicando o preço de venda unitário pela quantidade:
Subtotal = Preço de Venda × Quantidade

3. Frete Total
O frete por caixa é multiplicado pela quantidade apenas se o tipo de frete for CIF.
Frete Total = Frete por Caixa × Quantidade  (se Frete = CIF)
Quando o frete for FOB, ele é desconsiderado dos cálculos de lucro e ICMS-ST.

4. IPI (Imposto sobre Produtos Industrializados)
O valor do IPI é calculado sobre o subtotal, utilizando o percentual informado na planilha:
IPI Total = Subtotal × % IPI

5. Base de Cálculo do ICMS-ST
Conforme legislação vigente, a base de cálculo do ICMS-ST considera:
Subtotal
Valor do IPI
Não inclui frete, bonificação, comissão ou despesas
É aplicada a Margem de Valor Agregado (MVA) informada na planilha.
Base ICMS-ST = (Subtotal + IPI Total) × (1 + MVA)

6. Cálculo do ICMS-ST
O ICMS-ST a recolher é obtido pela diferença entre o ICMS calculado sobre a base do ICMS-ST e o ICMS próprio:
ICMS-ST = (Base ICMS-ST × % ICMS) - (Subtotal × % ICMS)
O resultado nunca será negativo (se negativo, considera-se zero).

7. Despesas Percentuais e Fixas
Somatório de percentuais da planilha:
ICMS, COFINS, PIS, Comissão, Bonificação, Contingência, Contrato, % Estratégico
Estas despesas são aplicadas ao preço de venda:
Despesas Reais = Preço de Venda × (Somatório dos Percentuais) × Quantidade + Frete Total

8. Lucro Bruto
Lucro Bruto = (Preço de Venda - Custo Total Unitário) × Quantidade - Despesas Reais

9. Lucro Líquido
Considerando carga tributária presumida de 34% (IRPJ + CSLL + Adicional):
Lucro Líquido = Lucro Bruto ÷ 1,34  (se positivo)

10. Impostos sobre Lucro
IRPJ = Lucro Líquido × 25%
CSLL = Lucro Líquido × 9%

11. Lucro Percentual
Apresentado como percentual sobre a Receita Bruta:
Lucro % = (Lucro Líquido ÷ Subtotal) × 100

12. Total Nota Fiscal
Soma do Subtotal, IPI e ICMS-ST:
Total NF = Subtotal + IPI Total + ICMS-ST
🧩 Regras & Premissas
Os campos de IPI, ICMS, COFINS, PIS, MVA e demais percentuais devem estar preenchidos corretamente na planilha.
O frete só impacta na análise quando o tipo for CIF.
A Bonificação, Comissão e Contrato não entram na base do ICMS-ST, sendo consideradas apenas na análise gerencial.
O cálculo do IRPJ e CSLL foi simplificado para 25% e 9% respectivamente, podendo ser ajustado conforme o regime fiscal da empresa.
O campo % Estratégico permite adicionar um mark-up adicional ao preço de venda.

