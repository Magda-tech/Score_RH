import sqlite3
import pandas as pd
import numpy as np

# Caminho para o arquivo .db
db = #"caminho do arquivo na máquina"

# Conecte ao arquivo .db
conn = sqlite3.connect(db)

# Consulta SQL para selecionar as variáveis necessárias para calcular o score
query = """

-- Este trecho seleciona o candidato (id_candidato), a experiência que ele teve (id_experiencia) e  calcula o tempo em que cada candidato trabalhou (tempo_experiencia_anos)
with ExperienciaDetalhada as (
    select
        e.id as id_experiencia,
        e.id_candidato,
        (JULIANDAY(e.dt_termino) - JULIANDAY(e.dt_inicio)) / 365 as tempo_experiencia_anos
    from
        experiencias e
),
-- O trecho abaixo traz as informações filtradas anteriormente e acrescenta as informações das demais tabelas referente à vaga e ao candidato e suas experiências
CandidatosPorArea as (
    select 
        c_v.id_candidato,
        c_v.id_vaga,
        c_v.pretensao_salarial,
        ed.tempo_experiencia_anos,
        ed.id_experiencia,
        case
        when vc.tempo_de_experiencia like '%anos%' then 
            cast(REPLACE(vc.tempo_de_experiencia, 'anos', '') as int) * 12
        when vc.tempo_de_experiencia like '%ano%' then 
            cast(REPLACE(vc.tempo_de_experiencia, 'ano', '') as int) * 12
        when vc.tempo_de_experiencia like '%meses%' then 
            cast(REPLACE(vc.tempo_de_experiencia, 'meses', '') as int)
             when vc.tempo_de_experiencia like '%Meses%' then 
            cast(REPLACE(vc.tempo_de_experiencia, 'meses', '') as int) end as tempo_de_experiencia_competencia,
        vc.id_competencia,
        vc.nivel_competencia,
        v.departamento,
        v.nivel_vaga,
        v.minimo_experiencia,
        v.salario_maximo,
        v.salario_minimo,
        v.localizacao,
        c.area,
        c.nome as nome_competencia,
        c.descricao as descricao_competencia,
        cd.endereco,
        round(cast(ce.tempo_competencia as float) / 30, 2) as tempo_competencia_meses,
        -- O trecho abaixo calcula o maior tempo de experiência em anos por candidato, área e id_experiencia que se refere a cada emprego que ele teve
        -- Filtro para saber o tempo máximo de experiência em anos de um candidato em uma área específica
       max(ed.tempo_experiencia_anos) over (partition by c_v.id_candidato, c.area, ed.id_experiencia) as max_tempo_experiencia_anos
    from 
        candidato_vaga c_v 
    left join
        ExperienciaDetalhada ed on ed.id_candidato = c_v.id_candidato
    left join
        competencia_experiencia ce on ed.id_experiencia = ce.id_experiencia
    left join
        competencias c on ce.id_competencia = c.id
    left join
        vagas v on v.id = c_v.id_vaga
    left join
        vagacompetencia vc on vc.id_vaga = c_v.id_vaga and vc.id_competencia = c.id
    left join
        candidatos cd on cd.id = c_v.id_candidato
    )
select
    cpa.id_vaga,
    cpa.departamento,
    cpa.nivel_vaga,
    substr(cpa.localizacao, instr(cpa.localizacao, '-') + 2) as localizacao,
    cpa.id_competencia,
    cpa.nivel_competencia,
    cpa.tempo_de_experiencia_competencia as minimo_competencia_meses,
    cpa.minimo_experiencia as minimo_experiencia_anos,
    cpa.tempo_competencia_meses as experiencia_competencia_meses,
    cpa.id_candidato,
    substr(cpa.endereco, instr(cpa.endereco, '/') + 2) as estado_candidato,
    cpa.id_experiencia,
    cpa.descricao_competencia,
    cpa.max_tempo_experiencia_anos as experiencia_anos,
    cpa.pretensao_salarial,
    cpa.salario_maximo,
    cpa.salario_minimo
from 
    CandidatosPorArea cpa
"""
# Executar a consulta e carregar os dados em um DataFrame
df = pd.read_sql_query(query, conn)


# Exibir os dados da consulta
#print("\nResultado da consulta:")
#print(df)

# Função para calcular o score salarial
def calcular_score_salarial(pretensao_salarial, salario_minimo, salario_maximo):
    # Substituir null
    salario_minimo = salario_minimo or 0
    salario_maximo = salario_maximo or 0
    
    
    if pretensao_salarial > salario_maximo:
        return 0 
    
    diferenca_minimo = abs(pretensao_salarial - salario_minimo)
    diferenca_maximo = abs(pretensao_salarial - salario_maximo)
    diferenca_salarial = max(diferenca_minimo, diferenca_maximo)
    
    salario_intervalo = salario_maximo - salario_minimo
    score_salario = max((1 - (diferenca_salarial / salario_intervalo)) * 100, 0) # lógica para pontuar mais baixo quanto mais próxima a pretensão estiver dos limites
    return score_salario

# Função para calcular o score de competências
def calcular_score_competencias(candidato_competencias, competencias_relevantes):
    score = 0
    for _, row in candidato_competencias.iterrows():
        descricao_competencia = row['descricao_competencia'] or ''  # Substituir nulos por string vazia
        tempo_competencia = row['experiencia_competencia_meses'] or 0  # Substituir nulos por zero

        if descricao_competencia in competencias_relevantes:
            experiencia_score = 100 if tempo_competencia > 60 else (tempo_competencia / 12) * 20 
    # 60 meses = 5 anos (especialista) | se tempo_competencia for < 60, a pontuação será proporcional por cada ano 

    # Aumentar o peso em 30% para competências que começam com "Atitude" (fit cultural)
            if descricao_competencia.startswith("Atitude"):
                experiencia_score *= 1.3
            
            score += experiencia_score

    return min(score, 100)


# Função para calcular o score de localização
def calcular_score_localizacao(candidato_estado, vaga_estado):
    estados_preferenciais = ['SC', 'PE', 'SP']

    # Recebe pontuação máxima quando a vaga é em um dos estados_preferenciais (preferem candidatos do mesmo estado da sede)  e o candidato mora em um dos estados_preferenciais
    if vaga_estado in estados_preferenciais and candidato_estado == vaga_estado:
        return 100
    # Recebe metade da pontuação quando a vaga é em um dos estados_preferenciais (preferem candidatos do mesmo estado da sede)  e o candidato não mora em um dos estados_preferenciais
    elif vaga_estado in estados_preferenciais and candidato_estado != vaga_estado:
        return 50
    # Recebe pontuação máxima quando a vaga não é em um dos estados_preferenciais (preferem candidatos do mesmo estado da sede) e o candidato mora num local diferente do local da vaga
    elif vaga_estado not in estados_preferenciais and candidato_estado != vaga_estado:
        return 100
    # Recebe pontuação máxima quando a vaga não é em um dos estados_preferenciais (preferem candidatos do mesmo estado da sede) e o candidato mora num local igual ao do local da vaga
    elif vaga_estado not in estados_preferenciais and candidato_estado == vaga_estado:
        return 100

def calcular_score_departamento(departamentos_candidato, num_vagas):
    if not departamentos_candidato:  # Se o conjunto estiver vazio, retornar zero
        return 0

    grupos_compatibilidade = [{"Dados", "Engenharia"}, {"Contabilidade", "Financeira"}]

    if num_vagas == 1:
        return 100 
    if num_vagas > 1 and any(departamentos_candidato.issubset(grupo) for grupo in grupos_compatibilidade):
        return 100
    return 50

    # Função para calcular o score total
def calcular_score_total(candidato_data, vaga_data, competencias_candidato, departamentos_candidato, num_vagas):
    # Obter o departamento da vaga
    departamento = vaga_data['departamento']
    
    # Obter competências relevantes para o departamento
    competencias_relevantes = df[df['departamento'] == departamento]['descricao_competencia'].unique().tolist()
    
    # Calcular o score de competências
    score_competencias = calcular_score_competencias(competencias_candidato, competencias_relevantes)
    #print(f"ID do Candidato: {id_candidato}, Competências Relevantes: {competencias_relevantes}")

    # Calcular o score salarial
    score_salarial = calcular_score_salarial(
        candidato_data['pretensao_salarial'], vaga_data['salario_minimo'], vaga_data['salario_maximo']
    )

    # Calcular o score de localização
    score_localizacao = calcular_score_localizacao(candidato_data['estado_candidato'], vaga_data['localizacao'])

    # Calcular o score de compatibilidade de departamento
    score_departamento = calcular_score_departamento(departamentos_candidato, num_vagas)

    #substituir valores null por zero
    score_competencias = np.nan_to_num(score_competencias, nan=0)
    score_salarial = np.nan_to_num(score_salarial, nan=0)
    score_localizacao = np.nan_to_num(score_localizacao, nan=0)
    score_departamento = np.nan_to_num(score_departamento, nan=0)
    score_total = (score_competencias * 0.25) + (score_salarial * 0.25 ) + (score_localizacao * 0.25) + (score_departamento * 0.25) # Soma dando o mesmo peso para os scores
    
    return min(score_total, 100)  # Limitar o score total a 100


# Criar DataFrame de scores
resultados = []

def calcular_scores(df):
    resultados = []

    for id_vaga, group in df.groupby('id_vaga'):
        vaga_data = group.iloc[0]

        for id_candidato, candidato_data in group.groupby('id_candidato'):
            candidato_info = candidato_data.iloc[0]
            
            competencias_candidato = candidato_data[['descricao_competencia', 'experiencia_competencia_meses']].fillna({'descricao_competencia': '', 'experiencia_competencia_meses': 0})
            departamentos_candidato = set(candidato_data['departamento'].fillna(''))
            num_vagas = len(group['id_vaga'].unique())

            score = calcular_score_total(candidato_info, vaga_data, competencias_candidato, departamentos_candidato, num_vagas)

            resultados.append({
                'id_vaga': id_vaga,
                'id_candidato': id_candidato,
                'score': score
            })

    scores_df = pd.DataFrame(resultados)
    return scores_df
conn.close()
