from graficos import *
import pandas as pd

"""
dados: DataFrame contendo os dados de contracheques a serem analisados
resultado: DataFrame contendo todos os alertas gerados
"""

def resumir_alertas(resultado, dados):
    # Quantitativos dos alertas
    print(f"caso_remuneracao == 'MAIOR': {resultado[resultado.caso_remuneracao == 'MAIOR'].orgao.count()}")
    print(f"caso_remuneracao == 'MENOR': {resultado[resultado.caso_remuneracao == 'MENOR'].orgao.count()}")
    print(f"caso_membros == 'MAIOR': {resultado[resultado.caso_membros == 'MAIOR'].orgao.count()}")
    print(f"caso_membros == 'MENOR': {resultado[resultado.caso_membros == 'MENOR'].orgao.count()}")

    print("Total de órgãos analisados: ", len(dados.orgao.unique().tolist()))
    print("Total de órgãos com alertas: ", len(resultado.orgao.unique().tolist()))
    
def visualizar_casos_remuneracao_maior(resultado):
    # Plotando gráfico com casos de remuneração MAIOR que 50% comparado à referência
    casos_maior = resultado[resultado.caso_remuneracao == 'MAIOR'].groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
    casos_maior['mes/ano'] = casos_maior.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
    plotar_grafico(casos_maior, 'mes/ano', 'quantidade_alertas',
                'Nº de alertas por mês/ano com remuneração acima da referência', 'grafico-rmaior.png', True)

    # Gráfico apenas com órgãos dos meses que excederam a média do gráfico anterior
    plotar_grafico_complementar(casos_maior, 'MAIOR', 'Órgãos dos meses que excederam a média (acima da referência)', 'grafico-rmaior-orgaos.png', resultado)

def visualizar_casos_remuneracao_menor(resultado):
    # Plotando gráfico com casos de remuneração MENOR que 50% comparado à referência
    casos_menor = resultado[resultado.caso_remuneracao == 'MENOR'].groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
    casos_menor['mes/ano'] = casos_menor.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
    plotar_grafico(casos_menor, 'mes/ano', 'quantidade_alertas',
                'Nº de alertas por mês/ano com remuneração abaixo da referência', 'grafico-rmenor.png', True)

    # Gráfico apenas com órgãos dos meses que excederam a média do gráfico anterior
    plotar_grafico_complementar(casos_menor, 'MENOR', 'Órgãos dos meses que excederam a média (abaixo da referência)', 'grafico-rmenor-orgaos.png', resultado)

def visualizar_casos_remuneracao(resultado):
    # Plotando gráfico com todos os casos de alertas de remuneração
    contagem_ocorrencias = resultado.drop('caso_membros', axis=1).dropna(subset=['caso_remuneracao'])
    contagem_ocorrencias = contagem_ocorrencias.groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
    contagem_ocorrencias['mes/ano'] = contagem_ocorrencias.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
    plotar_grafico(contagem_ocorrencias, 'mes/ano', 'quantidade_alertas',
                'Nº total de alertas por mês/ano', 'grafico-rgeral.png', True)
    
def visualizar_alertas_por_orgao(resultado):
    # Quantidade de alertas por órgão -> 
    # gráfico de barras agrupadas onde o eixo vertical é a quantidade de alertas e o eixo horizontal cada órgão
    # cada barra representa os casos MAIOR e MENOR, respectivamente.
    contagem_ocorrencias_por_orgao = resultado.groupby(['orgao', 'caso_remuneracao']).size().unstack(fill_value=0)
    contagem_ocorrencias_por_orgao = contagem_ocorrencias_por_orgao.reset_index()
    contagem_ocorrencias_por_orgao = pd.melt(contagem_ocorrencias_por_orgao, id_vars=['orgao'], var_name='caso_remuneracao', value_name='quantidade_alertas')
    plotar_grafico(contagem_ocorrencias_por_orgao, 'orgao', 'quantidade_alertas',
                'Nº total de alertas por órgão', 'grafico-orgaos.png', False)