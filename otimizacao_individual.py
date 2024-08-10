import pandas as pd
from gurobipy import Model, GRB, quicksum
import json

instancia = '3_depositos'

class Deposito:
    def __init__(self, id, w, Q, q, obras):
        self.id = id
        self.w = w  # Prioridades associadas às obras
        self.Q = Q  # Recursos disponíveis dos materiais
        self.q = q  # Quantidades de material t necessário para cada obra i
        self.M = len(w)  # Número total de obras
        self.T = len(Q)  # Número total de materiais
        self.x = None
        self.obj_val = None
        self.obras = obras  # Códigos das obras
        self.num_obras_associadas = 0
        self.num_obras_executadas = 0
        self.soma_prioridades_executadas = 0
        self.soma_prioridades_assoc = 0

    @classmethod
    def from_dataframes(cls, df_obras, df_depositos, deposito_id):
        df_obras_filtrado = df_obras[df_obras['COD_DEP'] == deposito_id]
        df_depositos_filtrado = df_depositos[df_depositos['COD_DEP'] == deposito_id]

        w = df_obras_filtrado.groupby('OBRA')['PESO'].first().tolist()
        Q = df_depositos_filtrado['ESTOQ_DPST'].tolist()

        # Pivot para obter a matriz q, preenchendo com zeros os valores ausentes
        materiais_comuns = df_obras_filtrado['COD_MAT'].isin(df_depositos_filtrado['COD_MAT'])
        df_obras_filtrado_comum = df_obras_filtrado[materiais_comuns]
        q = df_obras_filtrado_comum.pivot(index='OBRA', columns='COD_MAT', values='QTD_PEND').fillna(0)

        # Reordenar as colunas de q para corresponder à ordem dos materiais em Q
        q = q.reindex(columns=df_depositos_filtrado['COD_MAT'], fill_value=0).values.tolist()

        # Obter a lista de códigos de obras
        obras = df_obras_filtrado['OBRA'].unique().tolist()

        # Criar o objeto Deposito e armazenar o DataFrame filtrado
        deposito = cls(deposito_id, w, Q, q, obras)
        deposito.df_obras_filtrado = df_obras_filtrado
        deposito.num_obras_associadas = df_obras_filtrado['OBRA'].nunique()
        deposito.soma_prioridades_assoc = sum(deposito.w)  # Soma das prioridades das obras associadas

        return deposito

    def solve(self):
        # Criação do modelo Gurobi
        model = Model(f"Problema da Mochila - Deposito {self.id}")

        # Variáveis de decisão
        x = model.addVars(self.M, vtype=GRB.BINARY, name="x")

        # Função objetivo
        model.setObjective(quicksum(self.w[i] * x[i] for i in range(self.M)), GRB.MAXIMIZE)

        # Restrições de capacidade de material
        for t in range(self.T):
            model.addConstr(
                quicksum(self.q[i][t] * x[i] for i in range(self.M)) <= self.Q[t],
                name=f"Material_{t}"
            )

        # Otimização do modelo
        model.optimize()

        # Armazenar os resultados
        if model.status == GRB.OPTIMAL:
            self.x = [x[i].x for i in range(self.M)]
            self.obj_val = model.objVal
            self.num_obras_executadas = sum(self.x)
            self.soma_prioridades_executadas = sum(self.w[i] for i in range(self.M) if self.x[i] > 0)
        else:
            self.x = None
            self.obj_val = None

    def print_solution(self):
        if self.x is not None:
            print(f"Solução ótima encontrada para o Depósito {self.id}:")
            for i in range(self.M):
                print(f"x_{i} = {self.x[i]}")
            print(f"Valor da função objetivo: {self.obj_val}")
        else:
            print(f"Não foi encontrada uma solução ótima para o Depósito {self.id}.")

    def gerar_relacionamento_obras(self):
        obras_executadas = [self.obras[i] for i in range(self.M) if self.x[i] > 0]
        return {str(self.id): obras_executadas}


# Carregar os dados
df_obras = pd.read_excel(f'dados/{instancia}/Obras.xlsx')
df_depositos = pd.read_excel(f'dados/{instancia}/Estoque.xlsx')

df_obras['PESO'] = df_obras['PESO'].astype(str).str.replace(',', '.', regex=False).astype(float)
df_obras['QTD_PEND'] = df_obras['QTD_PEND'].astype(str).str.replace(',', '.', regex=False).astype(float)

depositos = {}
for deposito_id in df_obras['COD_DEP'].unique():
    depositos[deposito_id] = Deposito.from_dataframes(df_obras, df_depositos, deposito_id)

# Resolver o problema para cada depósito e armazenar resultados
resultados = []
obras_executadas = {}
for deposito in depositos.values():
    deposito.solve()
    resultados.append({
        "COD_DEP": deposito.id,
        "NUM_OBRAS_ASSOCIADAS": deposito.num_obras_associadas,
        "OBRAS_EXECUTADAS": deposito.num_obras_executadas,
        "SOMA_PRIORIDADES_EXECUTADAS": deposito.soma_prioridades_executadas,
        "SOMA_PRIORIDADES_ASSOCIADAS": deposito.soma_prioridades_assoc
    })
    relacionamento = deposito.gerar_relacionamento_obras()
    obras_executadas.update(relacionamento)

# Gerar DataFrame com os resultados
df_resultados = pd.DataFrame(resultados)

# Salvar os resultados em um arquivo CSV
df_resultados.to_csv(f'resultados/otimizacao_individual/{instancia}/compilado.csv', index=False)

# Salvar obras executadas
with open(f'resultados/otimizacao_individual/{instancia}/obras_executadas.json', 'w') as file:
    json.dump(obras_executadas, file, indent=4)

print(df_resultados)
