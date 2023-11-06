import seaborn as sns
import matplotlib.pyplot as plt

"""
Funções genéricas para geração de gráficos
"""

def plotar_grafico(dados, eixo_x, eixo_y, titulo, png, media):
    # Neste gráfico, utilizamos barras agrupadas, então a configuração é diferente
    if png == 'grafico-orgaos.png':
        plt.figure(figsize=(30,10))
        sns.barplot(data=dados, x=eixo_x,
                        y=eixo_y, palette=['#09C', 'red'], hue='caso_remuneracao').set(title = titulo)
    else:
        plt.figure(figsize=(20,10))
        sns.barplot(data=dados, x=eixo_x,
                        y=eixo_y, color='#09C').set(title = titulo)
    
    # Se "media" = true, então listaremos a média de alertas no gráfico
    if media:
        plt.axhline(y=dados.quantidade_alertas.mean(), color='red', linestyle=':', label='média de alertas')
        plt.legend()

    plt.xticks(rotation=60)
    plt.savefig(png, format='png')
    plt.clf()

# Este gráfico representa um complemento de um gráfico gerado anteriormente.
# e.g. quais órgãos estão presentes nos meses que ultrapassaram a média de alertas no gráfico anterior?
def plotar_grafico_complementar(dados, caso, titulo, png, resultado):
    meses_acima_da_media = dados[dados.quantidade_alertas > dados.quantidade_alertas.mean()]
    meses_acima_da_media = meses_acima_da_media['mes/ano'].tolist()
    orgaos = resultado.loc[resultado.caso_remuneracao == caso, ['orgao', 'ano', 'mes']]
    orgaos['mes/ano'] = orgaos.apply(lambda row: f"{row['mes']}/{row['ano']}", axis=1)
    orgaos = orgaos[orgaos['mes/ano'].isin(meses_acima_da_media)]
    orgaos = orgaos.groupby('orgao').size().reset_index(name='quantidade_alertas')

    plotar_grafico(orgaos, 'orgao', 'quantidade_alertas',
                titulo, png, True)