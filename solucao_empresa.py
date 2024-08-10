import pandas as pd

# Carregar os dados
df_obras = pd.read_excel('dados/completo/Obras.xlsx')
df_depositos = pd.read_excel('dados/completo/Estoque.xlsx')

# Ajustar os tipos de dados
df_obras['PESO'] = df_obras['PESO'].astype(str).str.replace(',', '.', regex=False).astype(float)

# Lista para armazenar os resultados
resultados = []

# Iterar sobre cada depósito
for deposito_id in df_obras['COD_DEP'].unique():
    # Filtrar as obras do depósito atual
    df_obras_filtrado = df_obras[df_obras['COD_DEP'] == deposito_id]

    # Número de obras associadas ao depósito
    num_obras_associadas = df_obras_filtrado['OBRA'].nunique()

    # Filtrar obras atendidas
    df_obras_atendidas = df_obras_filtrado[df_obras_filtrado['ATEND_OBRA'] == 1]

    # Calcular o número de obras executadas
    num_obras_executadas = df_obras_atendidas['OBRA'].nunique()

    # Calcular a soma das prioridades das obras executadas
    soma_prioridades_executadas = df_obras_atendidas.groupby('OBRA')['PESO'].first().sum()

    # Calcular a soma das prioridades de todas as obras
    soma_prioridades = df_obras_filtrado.groupby('OBRA')['PESO'].first().sum()

    # Armazenar os resultados
    resultados.append({
        "COD_DEP": deposito_id,
        "NUM_OBRAS_ASSOCIADAS": num_obras_associadas,
        "OBRAS_EXECUTADAS": num_obras_executadas,
        "SOMA_PRIORIDADES_EXECUTADAS": soma_prioridades_executadas,
        "SOMA_PRIORIDADES": soma_prioridades
    })

# Gerar DataFrame com os resultados
df_resultados = pd.DataFrame(resultados)

# Salvar os resultados em um arquivo CSV
df_resultados.to_csv('resultados/solucao_empresa/compilado.csv', index=False)

# Exibir os resultados
print(df_resultados)
