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

### Reconciliação de 2022–2025

A população de 2022–2025 foi reconciliada a partir de publicações oficiais. As referências temporais não são equivalentes:

- **2022 — Censo Demográfico:** valores do Censo 2022 conforme as páginas atuais do IBGE Cidades e Estados: [Ananindeua](https://www.ibge.gov.br/cidades-e-estados/pa/ananindeua.html), [Belém](https://www.ibge.gov.br/cidades-e-estados/pa/belem.html), [Benevides](https://www.ibge.gov.br/cidades-e-estados/pa/benevides.html), [Castanhal](https://www.ibge.gov.br/cidades-e-estados/pa/castanhal.html), [Marituba](https://www.ibge.gov.br/cidades-e-estados/pa/marituba.html), [Santa Bárbara do Pará](https://www.ibge.gov.br/cidades-e-estados/pa/santa-barbara-do-para.html) e [Santa Izabel do Pará](https://www.ibge.gov.br/cidades-e-estados/pa/santa-izabel-do-para.html).
- **2023 — valor de referência transportado:** a FAPESPA informa que repetiu para 2023 os valores de 2022 porque o IBGE não calculou estimativas populacionais municipais para 2023. Assim, os números de 2023 neste conjunto **não são estimativas independentes nem contagens realizadas em 2023**; repetem a população censitária de 2022 como denominador de referência para manter a taxa calculável. Fonte: [FAPESPA, tabela de população 2020–2024 e nota metodológica](https://www.fapespa.pa.gov.br/sistemas/anuario2024/tabelas/demografia/tab-1.1-populacao-total-estimativas-populacionais-e-censo-deografico-2020-a-2024.htm).
- **2024 — estimativas populacionais do IBGE**, divulgadas pela FAPESPA com referência em 1º de julho de 2024: [tabela FAPESPA 2020–2024](https://www.fapespa.pa.gov.br/sistemas/anuario2024/tabelas/demografia/tab-1.1-populacao-total-estimativas-populacionais-e-censo-deografico-2020-a-2024.htm).
- **2025 — estimativas populacionais do IBGE**, referência em 1º de julho de 2025, usando a versão atualizada do arquivo em 28 de agosto de 2026: [POP2025_20260828.pdf](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2025/POP2025_20260828.pdf).

| Município | 2022 — Censo | 2023 — repetição de 2022 | 2024 — estimativa | 2025 — estimativa |
|---|---:|---:|---:|---:|
| Ananindeua | 478.778 | 478.778 | 507.838 | 509.227 |
| Belém | 1.303.403 | 1.303.403 | 1.398.531 | 1.397.315 |
| Benevides | 63.567 | 63.567 | 68.191 | 68.962 |
| Castanhal | 192.256 | 192.256 | 207.603 | 209.126 |
| Marituba | 111.785 | 111.785 | 118.998 | 119.437 |
| Santa Bárbara do Pará | 21.087 | 21.087 | 22.288 | 22.530 |
| Santa Izabel do Pará | 73.019 | 73.019 | 78.317 | 79.195 |

O CSV foi atualizado com os valores acima e a coluna **taxa_internacoes_hidricas_10k** foi recalculada para os anos correspondentes pela fórmula **internacoes_hidricas_total / populacao × 10.000**. A alteração não muda os totais de internações nem valida sua proveniência.

## Saneamento

O CSV consolidado tem indicadores de saneamento ausentes em 2017, 2018, 2024 e 2025 e lacunas em outros município/ano. As ausências devem permanecer como campos vazios/ N/D, não ser convertidas em zero.

A documentação oficial do Ministério das Cidades informa a transição entre o SNIS até 2023 e o SINISA a partir da coleta referente a 2024. Ao integrar períodos, documentar separadamente sistema, indicador, unidade e referência temporal; não assumir continuidade metodológica automática. [SNIS/SINISA — área do prestador e municípios](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/snis/area-do-prestador-e-municipios).

## Saúde — SIH/DATASUS

O pipeline registrado em `scripts/build_iara_municipios_rmb.py` seleciona internações cujo diagnóstico principal pertence ao grupo CID-10 A00–A09 e agrega os registros por município de residência e ano. Na CID-10, A00–A09 corresponde a **doenças intestinais infecciosas** (incluindo, por exemplo, infecções bacterianas, doenças por protozoários, infecções virais e gastroenterite infecciosa presumível). Esse agrupamento **não prova que cada internação tenha sido transmitida pela água** nem permite atribuir sua causa individual ao saneamento. Fonte de classificação: [CID-10 brasileira — Ministério da Saúde/RNDS](https://fhir.saude.gov.br/rira/en/CodeSystem-BRCID10.html).

O DATASUS publica arquivos SIH/RD separados por local de internação e por local de residência; o pipeline procura arquivos `RDPA*.csv` e utiliza `MUNIC_RES`, ou seja, município de residência. A origem exata, os nomes e hashes dos arquivos usados na série consolidada ainda precisam ser inventariados. Referência de acesso: [DATASUS — Produção Hospitalar SIH/SUS](https://datasus.saude.gov.br/acesso-a-informacao/producao-hospitalar-sih-sus/).

O código de construção agora deixa explícitos erros de leitura/estrutura em vez de ignorar silenciosamente arquivos SIH inválidos, valida campos essenciais nas internações A00–A09 e preserva ausência de correspondência como valor ausente, não zero. Isso melhora o comportamento do ETL, mas não valida retroativamente os totais históricos já publicados. **As contagens da série consolidada continuam em auditoria até que os arquivos brutos, a cobertura temporal e possíveis sobreposições entre arquivos sejam conferidos.**

A taxa `taxa_internacoes_hidricas_10k` é calculada como `internacoes_hidricas_total / populacao * 10000` quando ambos os campos estão disponíveis e a população é positiva. A consistência aritmética da fórmula não comprova integridade da contagem de internações nem causalidade entre saneamento e saúde.

## Clima

O pipeline lê arquivos de uma estação INMET em Belém (A201), calcula precipitação anual e temperatura média, normaliza essas variáveis por min–max e obtém um índice médio. O mesmo valor anual é atribuído aos sete municípios. Portanto, `risco_climatico` deve ser interpretado como **índice climático exploratório regional baseado em uma estação**, não como risco municipal validado ou evidência de efeito sobre internações.

## Integridade e regras de interpretação

- A grade consolidada esperada é 7 municípios × 9 anos = 63 registros.
- `(cod_ibge, ano)` deve ser único.
- Um valor zero conhecido é diferente de um valor ausente.
- Não imputar valores ausentes sem fonte/método explicitamente documentados.
- Associações entre saneamento, saúde e clima permanecem descritivas; não demonstram causalidade.
- Os arquivos brutos referidos pelo pipeline não estão atualmente versionados neste repositório. A reprodução completa depende de recuperar esses arquivos ou documentar fontes de download, versão, data de extração e hashes.
