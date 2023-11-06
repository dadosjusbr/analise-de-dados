import postgres as p
import pandas as pd
import time
from graficos import *
from visualizar_resultado import *

start = time.time()

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

# Gerando csv com resultado dos alertas
resultado = resultado.sort_values(['orgao', 'ano', 'mes'])
resultado.to_csv('resultado.csv', index=False)

# Resumo quantitativo dos alertas
resumir_alertas(resultado, dados)

"""
Número de alertas que seriam emitidos por mês/ano -> 
gráfico de barras, onde o eixo vertical será o número de alertas emitidos e o eixo horizontal o rótulo mês/ano
"""
# Plotando gráfico com casos de remuneração MAIOR que 50% comparado à referência
visualizar_casos_remuneracao_maior(resultado)

# Plotando gráfico com casos de remuneração MENOR que 50% comparado à referência
visualizar_casos_remuneracao_menor(resultado)

# Plotando gráfico com todos os casos de alertas de remuneração
visualizar_casos_remuneracao(resultado)

# Quantidade de alertas por órgão -> 
# gráfico de barras onde o eixo vertical é a quantidade de alertas e o eixo horizontal cada órgão
visualizar_alertas_por_orgao(resultado)

end = time.time()
print(f"Tempo de execução: {end - start}")