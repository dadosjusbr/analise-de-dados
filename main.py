import postgres as p
import pandas as pd
from alertas import *
import os

conn = p.get_connection()

mes = int(os.environ["MONTH"])
ano = int(os.environ["YEAR"])

if ano != 2018:
    # ano anterior
    ano_comparativo = ano - 1
else:
    # ano posterior
    ano_comparativo = ano + 1

dados_mensais = p.consultar_db(
    conn, f"select id_orgao, sumario->'remuneracoes'->'total', sumario->'membros' from coletas where ano = {ano} and mes = {mes} and (procinfo::text='null' or procinfo is null) and atual = true")

dados_mensais = pd.DataFrame(dados_mensais, columns=[
                             "orgao", "total", "count_membros"]).to_numpy()

for orgao, total, count_membros in dados_mensais:
    dados_anuais = p.consultar_db(
        conn, f"select mes, sumario->'remuneracoes'->'total', sumario->'membros' from coletas where id_orgao = '{orgao}' and ano = {ano_comparativo} and (procinfo::text='null' or procinfo is null) and atual = true")
    dados_anuais = pd.DataFrame(dados_anuais, columns=[
                                "mes", "total", "count_membros"])


    media = ((total - dados_anuais.total.mean())
            * 100) / dados_anuais.total.mean()
    """
    PARA EVITAR VALORES MAIORES QUE OS CORRETOS:
    Valor total (soma de todas as remunerações de todos os membros) do órgão, naquele mês, 50% superior à média mensal daquele órgão no ano anterior.
    Para média: o parâmetro é o mesmo por 12 meses, atualizado quando muda o ano
    Dezembro: em razão das gratificações, o alerta passa a ser quando supera 100%
    """
    if (mes != 12 and media > 50) or (mes == 12 and media > 100):
        print("\n-----------------------------------------\n")
        print(f"Orgão: {orgao.upper()} | Ano: {ano} | Mês: {mes}\n")
        print(f"\n{orgao.upper()} ultrapassou {media:.1f}% em relação à média do ano anterior: atual: {total} || média anual: {dados_anuais.total.mean()}")
        analisar_orgao(conn, orgao, mes, ano)
    """
    PARA EVITAR VALORES MENORES QUE OS CORRETOS:
    Valor total (soma de todas as remunerações de todos os membros) de um mês, para cada órgão, 50% inferior à média mensal daquele órgão no ano anterior.
    Para média: o parâmetro é o mesmo por 12 meses, atualizado quando muda o ano
    """
    if media < -50:
        print("\n-----------------------------------------\n")
        print(f"Orgão: {orgao.upper()} | Ano: {ano} | Mês: {mes}\n")
        print(f"\n{orgao.upper()} obteve uma remuneração {abs(media):.1f}% inferior à média do ano anterior: atual: {total} || média anual: {dados_anuais.total.mean()}")
        """
        Número de membros de cada órgão (count unique) representar menos de 50% da média de membros daquele órgão no ano anterior.
        """
        if count_membros < dados_anuais.count_membros.mean()/2:
            print(
                f"\n{orgao.upper()} | membros: {count_membros} | média: {dados_anuais.count_membros.mean()}")
        analisar_orgao(conn, orgao, mes, ano)
