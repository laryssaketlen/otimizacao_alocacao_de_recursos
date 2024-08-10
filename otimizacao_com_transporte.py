import pandas as pd
import numpy as np
import time
from gurobipy import Model, GRB, quicksum
import json

instancia = '10_depositos'

t1 = time.time()
# Carregar os dados
df_obras = pd.read_excel(f'dados/{instancia}/Obras.xlsx')
df_depositos = pd.read_excel(f'dados/{instancia}/Estoque.xlsx')

print(f'{time.time() - t1} segundos para ler os arquivos.')

df_obras.set_index(['OBRA', 'COD_MAT'])
df_depositos.set_index(['COD_DEP', 'COD_MAT'])

df_obras['PESO'] = df_obras['PESO'].astype(str).str.replace(',', '.', regex=False).astype(float)
df_obras['QTD_PEND'] = df_obras['QTD_PEND'].astype(str).str.replace(',', '.', regex=False).astype(float)

# Parâmetros e variáveis de decisão
obras = df_obras['OBRA'].unique().tolist()
depositos = df_depositos['COD_DEP'].unique().tolist()
materiais = df_depositos['COD_MAT'].unique().tolist()


# Prioridades
w = {obra: df_obras[df_obras['OBRA'] == obra]['PESO'].values[0] for obra in obras}


Qs = df_depositos.groupby(['COD_DEP', 'COD_MAT'])
Q = {}
for df in Qs:
    Q[df[0][0], int(df[0][1])] = 0 if df[1]['ESTOQ_DPST'].empty else df[1]['ESTOQ_DPST'].values[0]


# Quantidade de material necessária para cada obra
qs = df_obras.groupby(['OBRA', 'COD_MAT'])
q = {}
for df in qs:
    q[df[0][0], int(df[0][1])] = 0 if df[1]['QTD_PEND'].empty else df[1]['QTD_PEND'].values[0]

# Custo de transporte gerado aleatoriamente
np.random.seed(42)
C = {(d1, d2, mat): np.random.randint(1, 5) for d1 in depositos for d2 in depositos for mat in materiais if d1 != d2}


t1 = time.time()

# Criação do modelo Gurobi
model = Model("Problema da Mochila Expandido")

# Variáveis de decisão
x = model.addVars(obras, depositos, vtype=GRB.BINARY, name="x")
t = model.addVars(depositos, depositos, materiais, vtype=GRB.CONTINUOUS, name="t")

print(f'{time.time() - t1} segundos para criar as variáveis de decisão.')

t1 = time.time()

# Função objetivo
model.setObjective(
    quicksum(w[obra] * x[obra, d] for obra in obras for d in depositos) -
    quicksum(C[d1, d2, mat] * t[d1, d2, mat] for d1 in depositos for d2 in depositos for mat in materiais if d1 != d2),
    GRB.MAXIMIZE
)

print(f'{time.time() - t1} - segundos para criar a função objetivo.')

t1 = time.time()

# Restrições de capacidade e transporte
for d1 in depositos:
    for d2 in depositos:
        if d1 != d2:
            for m in materiais:
                # Calcula a demanda no depósito d1
                demanda_d1 = quicksum(q.get((obra, m), 0) * x[obra, d1] for obra in obras)

                # Quantidade de material transportada para e de d1
                entrada_d1 = quicksum(t[d2, d1, m] for d2 in depositos if d2 != d1)
                saida_d1 = quicksum(t[d1, d1_alt, m] for d1_alt in depositos if d1_alt != d1)

                # Capacidade disponível e recebida
                capacidade_disponivel_d1 = Q.get((d1, m), 0)

                # Adiciona a restrição unificada
                model.addConstr(
                    demanda_d1 <= capacidade_disponivel_d1 + entrada_d1 - saida_d1,
                    name=f"Restricao_Unificada_{d1}_{d2}_{m}"
                )

print(f'{time.time() - t1} - segundos para criar as restrições de transporte.')

t1 = time.time()

# Restrições para alocação correta das obras
for obra in obras:
    depo_origem = df_obras[df_obras['OBRA'] == obra]['COD_DEP'].values[0]
    model.addConstr(x[obra, depo_origem] <= 1, name=f"Alocacao_Obra_{obra}_{depo_origem}")

    # Restrições para garantir que a obra seja alocada no depósito de origem
    for d in depositos:
        if d != depo_origem:
            model.addConstr(x[obra, d] == 0, name=f"Sem_Alocacao_Obra_{obra}_{d}")

print(f'{time.time() - t1} segundos para criar grupo 2 de restrições.')

t1 = time.time()

# Cada obra deve ser atribuída a no máximo um depósito
for obra in obras:
    model.addConstr(quicksum(x[obra, d] for d in depositos) <= 1, name=f"Obra_{obra}")

print(f'{time.time() - t1} segundos para criar grupo 3 de restrições')

t1 = time.time()

# Otimização do modelo
model.optimize()

print(f'{time.time() - t1} segundos para resolver o problema.')

t1 = time.time()

# Verificar o status do modelo
if model.status == GRB.OPTIMAL:
    print("Solução ótima encontrada")
else:
    print(f"Status do modelo: {model.status}")

# Armazenar os resultados
resultados = []
total_material_transportado = 0

resultado_obras_executadas = {}
transportes = []

if model.status == GRB.OPTIMAL:
    for d in depositos:
        obras_executadas = [obra for obra in obras if x[obra, d].x > 0.5]
        num_obras_executadas = len(obras_executadas)
        soma_prioridades_executadas = sum(w[obra] for obra in obras_executadas)
        num_obras_associadas = df_obras[df_obras['COD_DEP'] == d]['OBRA'].nunique()
        soma_prioridades_associadas = df_obras[df_obras['COD_DEP'] == d].groupby('OBRA')['PESO'].first().sum()
        material_enviado = 0
        material_recebido = 0

        for d1 in depositos:
            if d != d1:
                for m in materiais:
                    material_recebido += t[d1, d, m].x
                    material_enviado += t[d, d1, m].x
                    total_material_transportado += t[d, d1, m].x

                    # Adicionar transporte realizado
                    if t[d, d1, m].x > 0:
                        transportes.append({
                            "DEPOSITO ORIGEM": d,
                            "MATERIAL": m,
                            "DEPOSITO DESTINO": d1,
                            "QUANTIDADE": t[d, d1, m].x
                        })

        resultados.append({
            "COD_DEP": d,
            "NUM_OBRAS_ASSOCIADAS": num_obras_associadas,
            "OBRAS_EXECUTADAS": num_obras_executadas,
            "SOMA_PRIORIDADES_EXECUTADAS": soma_prioridades_executadas,
            "SOMA_PRIORIDADES": soma_prioridades_associadas,
            "MATERIAL_RECEBIDO": material_recebido,
            "MATERIAL_ENVIADO": material_enviado,
        })

        # Adicionar relacionamento de obras
        resultado_obras_executadas[str(d)] = obras_executadas

    # Adicionar a linha com o valor da função objetivo e o total de material transportado
    resultados.append({
        "COD_DEP": "Função objetivo:",
        "NUM_OBRAS_ASSOCIADAS": model.objVal,
        "OBRAS_EXECUTADAS": "",
        "SOMA_PRIORIDADES_EXECUTADAS": "TOTAL_MATERIAL_TRANSPORTADO",
        "SOMA_PRIORIDADES": total_material_transportado,
        "MATERIAL_RECEBIDO": "",
        "MATERIAL_ENVIADO": "",
    })

    # Gerar DataFrame com os resultados
    df_resultados = pd.DataFrame(resultados)

    # Salvar os resultados em um arquivo CSV
    df_resultados.to_csv(f'resultados/otimizacao_com_transporte/{instancia}/compilado.csv', index=False)

    # Gerar DataFrame com os transportes
    df_transportes = pd.DataFrame(transportes)

    # Salvar os transportes em um arquivo CSV
    df_transportes.to_csv(f'resultados/otimizacao_com_transporte/{instancia}/transportes.csv', index=False)

    # Salvar o relacionamento de obras em um arquivo JSON
    with open(f'resultados/otimizacao_com_transporte/{instancia}/obras_executadas.json', 'w') as json_file:
        json.dump(resultado_obras_executadas, json_file)

    print(f'{time.time() - t1} segundos para salvar os resultados.')

    # Exibir os resultados
    print(f"Função objetivo: {model.objVal}")
    print(f"Total de material transportado: {total_material_transportado}")
else:
    print("O modelo não encontrou uma solução ótima.")
