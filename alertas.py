import postgres as p
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import seaborn as sns
import matplotlib.pyplot as plt

# Busca anomalias entre as remunerações
def busca_anomalias(conn, orgao, ano, mes):
    contracheques = p.consultar_db(
        conn, f"SELECT id, nome, remuneracao FROM contracheques WHERE orgao = '{orgao}' and ano = {ano} and mes = {mes}")
    contracheques = pd.DataFrame(contracheques, columns=[
        'id', 'nome', 'remuneracao'])

    random_state = np.random.RandomState(42)
    model = IsolationForest(contamination=float(0.05),
                            random_state=random_state)

    model.fit(contracheques[['remuneracao']])

    # print(model.get_params())

    contracheques['scores'] = model.decision_function(
        contracheques[['remuneracao']])

    contracheques['anomaly_score'] = model.predict(
        contracheques[['remuneracao']])

    contracheques[contracheques['anomaly_score'] == -1].head()

    sns.scatterplot(data=contracheques, x='scores',
                    y='remuneracao', hue='anomaly_score').set(title = f"{orgao.upper()} {mes}/{ano}")
    plt.savefig(f'{orgao}-{ano}-{mes}.png', format='png')
    plt.clf()

    anomalias = contracheques[contracheques['anomaly_score'] == -1]
    print("\nPossíveis anomalias:")
    print(anomalias[['nome', 'remuneracao']].sort_values(
        ['remuneracao'], ascending=False, inplace=False))

    return contracheques


"""
Nome = 0
Erro mais frequente, quando o CNJ coloca um agregador 0
"""
def dados_agregados(contracheques):
    print("\nPossui dados agregados:")
    print('0' in contracheques.nome.values)


"""
Contar o número de membros do órgão e contar o número de ocorrências do lançamento tipo "subsídios".
Em tese, deve ser idêntico ou a contagem de membros ser maior (caso de resquícios de pagamentos de indenizações, etc).
Se a contagem de SUBÍDIOS for maior (podemos colocar uma margem de 20% sobre a contagem de nomes), levantar um alerta para o órgão, pois podem estar ocorrendo subsídios duplicados.
"""
def cnj_subsidios(conn, orgao, mes, ano, contracheques):
    for prefixo in ['tj', 'tre', 'trt', 'st']:
        if prefixo in orgao:
            itens = p.consultar_db(
                conn, f"SELECT item FROM remuneracoes WHERE orgao = '{orgao}' AND mes = {mes} AND ano = {ano}")
            itens = pd.DataFrame(itens, columns=['item'])
            print("\nPossui quantidade de subsídios acima do número de membros:")
            print(itens[itens.item == 'Subsídio'].count()
                  > contracheques.id.count())


"""
Objetivo: pegar lançamentos duplicados (chegamos a pegar 10 auxílios-alimentação em um único mês para cada membro de um órgão).
"""
def contador_rubricas(conn, orgao, mes, ano):
    rubricas_por_membro = p.consultar_db(
        conn, f"SELECT id_contracheque, count(item), count(distinct(item)) FROM remuneracoes WHERE orgao = '{orgao}' AND mes = {mes} AND ano = {ano} AND tipo != 'D' GROUP BY id_contracheque")
    rubricas_por_membro = pd.DataFrame(rubricas_por_membro, columns=[
        'id_contracheque', 'count_item', 'distinct_item'])

    rubricas = rubricas_por_membro[rubricas_por_membro.count_item !=
                                   rubricas_por_membro.distinct_item]
    print("\nPossui lançamentos duplicados: ", not rubricas.empty)
    if not rubricas.empty:
        print(rubricas)


def analisar_orgao(conn, orgao, mes, ano):
    contracheques = busca_anomalias(conn, orgao, ano, mes)
    dados_agregados(contracheques)
    cnj_subsidios(conn, orgao, mes, ano, contracheques)
    contador_rubricas(conn, orgao, mes, ano)
