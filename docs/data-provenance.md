# Proveniência e cobertura dos dados — IARA Data Hub

**Última revisão:** 27 de outubro de 2026

Este documento identifica o que foi conferido e o que ainda exige rastreabilidade. O fato de um valor estar no CSV consolidado não comprova, por si só, que sua fonte e método foram validados.

## População municipal

### Fonte verificada para 2017–2021

A tabela **“População Total e Estimativas Populacionais, Pará e municípios — 2017 a 2021”**, publicada pela FAPESPA, declara como fonte o IBGE — Estimativas Populacionais. Fonte primária consultada: [FAPESPA, tabela 1.1 (2017–2021)](https://www.fapespa.pa.gov.br/sistemas/anuario2021/tabelas/demografia/tab-1.1-populacao-total-e-estimativas-populacionais-2017-a-2021.htm).

Os valores abaixo foram conferidos na coluna de 2017 dessa tabela e aplicados ao CSV. As colunas de população dos anos 2018–2021 também são reproduzidas pela mesma tabela. São **estimativas anuais de população**, não contagens censitárias para todos os anos.

| Município | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---:|---:|---:|---:|---:|
| Ananindeua | 516.057 | 525.566 | 530.598 | 535.547 | 540.410 |
| Belém | 1.452.275 | 1.485.732 | 1.492.745 | 1.499.641 | 1.506.420 |
| Benevides | 60.990 | 61.689 | 62.737 | 63.768 | 64.780 |
| Castanhal | 195.253 | 198.294 | 200.793 | 203.251 | 205.667 |
| Marituba | 127.858 | 129.321 | 131.521 | 133.685 | 135.812 |
| Santa Bárbara do Pará | 20.492 | 20.704 | 21.079 | 21.449 | 21.811 |
| Santa Izabel do Pará | 68.836 | 69.746 | 70.801 | 71.837 | 72.856 |

### Taxa derivada para 2017–2021

Para esses anos, `taxa_internacoes_hidricas_10k` foi recalculada pela expressão:

`internacoes_hidricas_total / populacao * 10000`

A correção ajusta o denominador populacional e a taxa matemática derivada. **Não valida os totais de internações**: a extração SIH/DATASUS, os arquivos de entrada e os filtros ainda precisam ser reproduzidos e auditados.

### Situação de 2022–2025

Os registros de população de 2022–2025 permanecem em revisão de proveniência. A versão anterior de `scripts/patch_data.py` aplicava um único mapa populacional a 2023 e preenchia qualquer outro ano com população zero usando os mesmos números. Essa regra foi removida. O script atualizado trabalha exclusivamente com os anos 2017–2021 cobertos pela fonte citada e deixa anos posteriores intocados.

Não reutilizar valores censitários ou de um ano para preencher outro ano sem registrar fonte, referência temporal e método. As estimativas anuais e os resultados censitários precisam ser identificados como conceitos distintos.

## Saneamento

O CSV consolidado tem indicadores de saneamento ausentes em 2017, 2018, 2024 e 2025 e lacunas em outros município/ano. As ausências devem permanecer como campos vazios/ N/D, não ser convertidas em zero.

A documentação oficial do Ministério das Cidades informa a transição entre o SNIS até 2023 e o SINISA a partir da coleta referente a 2024. Ao integrar períodos, documentar separadamente sistema, indicador, unidade e referência temporal; não assumir continuidade metodológica automática. [SNIS/SINISA — área do prestador e municípios](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/area-do-prestador-e-municipios).

## Saúde

O pipeline registrado em `scripts/build_iara_municipios_rmb.py` filtra o campo `DIAG_PRINC` por prefixo `A0` e agrega por município de residência e ano. Ainda é necessário documentar os arquivos SIH/DATASUS usados, datas de extração, cobertura, critérios de inclusão e limitações. Até a conferência dessas fontes, tratar os totais e a taxa derivada como dados em auditoria.

## Clima

O pipeline lê arquivos de uma estação INMET em Belém (A201), calcula precipitação anual e temperatura média, normaliza essas variáveis por min–max e obtém um índice médio. O mesmo valor anual é atribuído aos sete municípios. Portanto, `risco_climatico` deve ser interpretado como **índice climático exploratório regional baseado em uma estação**, não como risco municipal validado ou evidência de efeito sobre internações.

## Integridade e regras de interpretação

- A grade consolidada esperada é 7 municípios × 9 anos = 63 registros.
- `(cod_ibge, ano)` deve ser único.
- Um valor zero conhecido é diferente de um valor ausente.
- Não imputar valores ausentes sem fonte/método explicitamente documentados.
- Associações entre saneamento, saúde e clima permanecem descritivas; não demonstram causalidade.
- Os arquivos brutos referidos pelo pipeline não estão atualmente versionados neste repositório. A reprodução completa depende de recuperar esses arquivos ou documentar fontes de download, versão, data de extração e hashes.
