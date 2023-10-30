import postgres as p
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import time

start = time.time()

def plotar_grafico(dados, eixo_x, eixo_y, titulo, png, media):
    # Neste gráfico, utilizammos barras agrupadas, então a configuração é diferente
    if png == 'grafico-orgaos.png':
        plt.figure(figsize=(30,10))
        sns.barplot(data=dados, x=eixo_x,
                        y=eixo_y, palette=['#09C', 'red'], hue='caso_remuneracao').set(title = titulo)
    else:
        plt.figure(figsize=(20,10))
        sns.barplot(data=dados, x=eixo_x,
                        y=eixo_y, color='#09C').set(title = titulo)
    
    if media:
        plt.axhline(y=dados.quantidade_alertas.mean(), color='red', linestyle=':', label='média de alertas')
        plt.legend()

    plt.xticks(rotation=60)
    plt.savefig(png, format='png')
    plt.clf()

def grafico_complemento(dados, caso, titulo, png):
    meses_acima_da_media = dados[dados.quantidade_alertas > dados.quantidade_alertas.mean()]
    meses_acima_da_media = meses_acima_da_media['mes/ano'].tolist()
    orgaos = resultado.loc[resultado.caso_remuneracao == caso, ['orgao', 'ano', 'mes']]
    orgaos['mes/ano'] = orgaos.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
    orgaos = orgaos[orgaos['mes/ano'].isin(meses_acima_da_media)]
    orgaos = orgaos.groupby('orgao').size().reset_index(name='quantidade_alertas')
    plotar_grafico(orgaos, 'orgao', 'quantidade_alertas',
                titulo, png, True)

conn = p.get_connection()

dados = p.consultar_db(conn, """select id_orgao, c.mes, c.ano, 
                       sumario->'membros', 
                       sumario->'remuneracao_base'->'total', 
                       sumario->'outras_remuneracoes'->'total', 
                       sumario->'descontos'->'total',
                       sumario->'remuneracoes'->'total' from coletas c 
                       where atual = true and (procinfo is null or procinfo::text = 'null')""")

dados = pd.DataFrame(dados, columns=['orgao','mes','ano','membros','base', 'outras', 'descontos', 'remuneracao_liquida']).fillna(0)
dados.to_csv('dados-analisados.csv')

resultado = pd.DataFrame(columns=['orgao','mes','ano', 'ano_comparado', 'remuneracao_liquida', 'remuneracao_comparada', 'percentual_diff_remuneracao', 'caso_remuneracao', 'membros', 'quant_membros_comparada', 'percentual_diff_membros', 'caso_membros'])

for orgao, mes, ano, membros, remuneracao_liquida in dados[['orgao', 'mes', 'ano', 'membros', 'remuneracao_liquida']].to_numpy():
    # Pegamos os dados para o respectivo mês a ser analisado nos demais anos
    dados_por_mes = dados[(dados.orgao == orgao) & (dados.mes == mes) & (dados.ano == ano - 1)]
    percentual_media = ((remuneracao_liquida - dados_por_mes.remuneracao_liquida.mean()) * 100) / dados_por_mes.remuneracao_liquida.mean()
    percentual_media_membros = ((membros - dados_por_mes.membros.mean()) * 100) / dados_por_mes.membros.mean()

    alerta = pd.DataFrame({'orgao': [orgao],
              'mes': [mes],
              'ano': [ano],
              'ano_comparado': [ano - 1],
              'remuneracao_liquida': [remuneracao_liquida],
              'remuneracao_comparada': [dados_por_mes.remuneracao_liquida.mean()],
              'percentual_diff_remuneracao': [percentual_media],
              'membros': [membros],
              'quant_membros_comparada': [dados_por_mes.membros.mean()],
              'percentual_diff_membros': [percentual_media_membros],
            })

    if percentual_media > 50:
        alerta['caso_remuneracao'] = 'MAIOR'
    
    if percentual_media < -50:
        alerta['caso_remuneracao'] = 'MENOR'
    
    if percentual_media_membros > 50:
        alerta['caso_membros'] = 'MAIOR'
    
    if percentual_media_membros < -50:
        alerta['caso_membros'] = 'MENOR'
        
    if 'caso_remuneracao' in alerta.keys() or 'caso_membros' in alerta.keys():
        resultado = pd.concat([resultado, alerta], ignore_index=True)
        
print(f"caso_remuneracao == 'MAIOR': {resultado[resultado.caso_remuneracao == 'MAIOR'].orgao.count()}")
print(f"caso_remuneracao == 'MENOR': {resultado[resultado.caso_remuneracao == 'MENOR'].orgao.count()}")
print(f"caso_membros == 'MAIOR': {resultado[resultado.caso_membros == 'MAIOR'].orgao.count()}")
print(f"caso_membros == 'MENOR': {resultado[resultado.caso_membros == 'MENOR'].orgao.count()}")

# Gerando csv com resultado dos alertas
resultado = resultado.sort_values(['orgao', 'ano', 'mes'])
resultado.to_csv('resultado.csv', index=False)
print(len(dados.orgao.unique().tolist()))
print(len(resultado.orgao.unique().tolist()))

"""
Número de alertas que seriam emitidos por mês/ano -> 
gráfico de barras, onde o eixo vertical será o número de alertas emitidos e o eixo horizontal o rótulo mês/ano
"""
# Plotando gráfico com casos de remuneração MAIOR que 50% e/ou 100% comparado à referência
casos_maior = resultado[resultado.caso_remuneracao == 'MAIOR'].groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
casos_maior['mes/ano'] = casos_maior.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
plotar_grafico(casos_maior, 'mes/ano', 'quantidade_alertas',
               'Nº de alertas por mês/ano com remuneração acima da referência', 'grafico-rmaior.png', True)
# Gráfico apenas com órgãos dos meses que excederam a média do gráfico anterior
grafico_complemento(casos_maior, 'MAIOR', 'Órgãos dos meses que excederam a média (acima da referência)', 'grafico-rmaior-orgaos.png')

# Plotando gráfico com casos de remuneração MENOR que 50% comparado à referência
casos_menor = resultado[resultado.caso_remuneracao == 'MENOR'].groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
casos_menor['mes/ano'] = casos_menor.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
plotar_grafico(casos_menor, 'mes/ano', 'quantidade_alertas',
               'Nº de alertas por mês/ano com remuneração abaixo da referência', 'grafico-rmenor.png', True)

# Gráfico apenas com órgãos dos meses que excederam a média do gráfico anterior
grafico_complemento(casos_menor, 'MENOR', 'Órgãos dos meses que excederam a média (abaixo da referência)', 'grafico-rmenor-orgaos.png')

# Plotando gráfico com todos os casos de alertas de remuneração
contagem_ocorrencias = resultado.drop('caso_membros', axis=1).dropna(subset=['caso_remuneracao'])
contagem_ocorrencias = contagem_ocorrencias.groupby(['ano', 'mes']).size().reset_index(name='quantidade_alertas')
contagem_ocorrencias['mes/ano'] = contagem_ocorrencias.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
plotar_grafico(contagem_ocorrencias, 'mes/ano', 'quantidade_alertas',
               'Nº total de alertas por mês/ano', 'grafico-rgeral.png', True)

"""
Quantidade de alertas por órgão -> 
gráfico de barras onde o eixo vertical é a quantidade de alertas e o eixo horizontal cada órgão
"""
contagem_ocorrencias_por_orgao = resultado.groupby(['orgao', 'caso_remuneracao']).size().unstack(fill_value=0)
contagem_ocorrencias_por_orgao = contagem_ocorrencias_por_orgao.reset_index()
contagem_ocorrencias_por_orgao = pd.melt(contagem_ocorrencias_por_orgao, id_vars=['orgao'], var_name='caso_remuneracao', value_name='quantidade_alertas')
plotar_grafico(contagem_ocorrencias_por_orgao, 'orgao', 'quantidade_alertas',
               'Nº total de alertas por órgão', 'grafico-orgaos.png', False)

end = time.time()
print(f"Tempo de execução: {end - start}")