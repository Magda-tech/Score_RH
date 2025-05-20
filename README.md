
# 🧠 Sistema de Cálculo de Score de Candidatos

Este projeto tem como objetivo calcular um **score de compatibilidade** entre candidatos e vagas de emprego com base em diversos critérios, utilizando Python e SQLite. É voltado para auxiliar processos de recrutamento e seleção, ranqueando candidatos conforme sua aderência técnica, salarial e geográfica à vaga.

## 🔍 Funcionalidades

- Extração de dados relacionais de um banco SQLite contendo informações sobre candidatos, experiências, competências e vagas.
- Cálculo de **score salarial**, baseado na diferença entre pretensão e faixa da vaga.
- Avaliação de **competências técnicas** com peso extra para soft skills (ex.: "Atitude").
- Análise de **localização geográfica** entre vaga e residência do candidato.
- Verificação de **compatibilidade entre departamentos**.
- Geração de um **score total ponderado** para cada candidato por vaga.

## 🛠 Tecnologias utilizadas

- Python 3.x
- Pandas
- NumPy
- SQLite3

## 📁 Estrutura

- `score_rh.py`: script principal que carrega os dados do banco, realiza os cálculos e retorna um DataFrame com os scores dos candidatos por vaga.
- Banco de dados `.db`: não incluído no repositório, mas esperado no caminho local definido na variável `db`.

## 🧮 Fórmula do Score Total

O score final é a média ponderada de quatro critérios:

- 25% Competências técnicas
- 25% Pretensão salarial
- 25% Localização
- 25% Departamento

Cada um dos critérios retorna um valor entre 0 e 100, e o score final também é limitado a 100.

## 📌 Observações

- O caminho do banco de dados está fixo e pode precisar ser ajustado antes da execução.
- O script não realiza escrita em banco ou exportação de resultados — apenas gera os scores em memória com um DataFrame.

## ✅ Exemplo de uso

```python
df_scores = calcular_scores(df)
print(df_scores.head())
```

## 📄 Licença

Este projeto está disponível sob a [Licença MIT](LICENSE).
