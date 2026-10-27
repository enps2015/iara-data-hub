# 🌊 IARA Data Hub

**Indicadores de Água, Resiliência e Adaptação – Região Metropolitana de Belém**

![IARA Data Hub Cover](img/iara_cover.png)

**Demonstração online:** [Abrir o IARA Data Hub ↗](https://enps2015.github.io/iara-data-hub/)

![Status](https://img.shields.io/badge/Status-Ativo-brightgreen)
![Dados](https://img.shields.io/badge/Dados-2017--2025-blue)
![Licença](https://img.shields.io/badge/Licença-CC_BY_4.0-orange)

## 📌 Sobre o Projeto

O **IARA Data Hub** é um observatório de dados sobre água, saneamento e saúde na Região Metropolitana de Belém (RMB), criado no contexto pós-COP30.

> _"Belém virou vitrine global com a COP30. O IARA mostra o que esse legado significa — ou não — para a água, o esgoto e a saúde na Região Metropolitana."_

### 🎯 Objetivo

Traduzir dados públicos dispersos em uma narrativa visual que conecta **saneamento, saúde e clima** na Amazônia urbana, permitindo:

- Vigilância cidadã sobre indicadores essenciais
- Análise crítica do legado da COP30
- Identificação de lacunas de dados e desigualdades

---

## 💡 Motivação

A COP30 trouxe Belém aos holofotes globais como "capital climática". BRT, parques, macrodrenagem e bilhões em fundos verdes foram anunciados. Mas enquanto as manchetes celebravam obras de infraestrutura, uma pergunta permanecia sem resposta:

> **"O que esses investimentos significam para quem ainda convive com esgoto a céu aberto, água intermitente e infecções cujo risco pode ser reduzido por água segura e saneamento?"**

Como profissional de dados e morador da Amazônia, percebi que **os dados existiam, mas estavam dispersos**. O SNIS tem informações sobre saneamento, o DATASUS sobre internações, o IBGE sobre população — mas ninguém estava conectando esses pontos para contar a história completa.

O IARA nasceu dessa necessidade: **um observatório crítico que não repete discursos oficiais, mas mostra a distância entre promessa e realidade através de dados.**

---

## 🔍 O Que Este Projeto Demonstra

### Padrões exploratórios a investigar

- **Saneamento × Saúde**: o projeto permite explorar associações entre cobertura de esgoto e internações hospitalares cujo diagnóstico principal está no grupo CID-10 A00–A09 (doenças intestinais infecciosas). Esse agrupamento não identifica, por si só, transmissão pela água nem estabelece causalidade.
- **Lacunas de dados**: a série consolidada abrange 2017–2025, mas a disponibilidade varia conforme o indicador e o ano. Em 2023, três dos sete municípios não têm coleta de esgoto informada; comparações entre indicadores devem usar apenas registros compatíveis e informar a cobertura efetiva.
- **Diferenças entre municípios**: as visualizações permitem comparar padrões observados na Região Metropolitana de Belém. A classificação em quadrantes ou zonas é relativa aos dados e critérios escolhidos, não um diagnóstico absoluto de qualidade sanitária.

**Nota de proveniência temporal:** a série populacional foi reconciliada com estimativas oficiais de 2017–2021, população censitária de 2022, repetição declarada desse valor em 2023 e estimativas oficiais de 2024–2025. A cobertura de saneamento é uma questão separada: os indicadores correspondentes estão ausentes em 2017, 2018, 2024 e 2025 no CSV atual; esses campos ausentes não devem ser interpretados como projeções nem como zero.

### Insights visuais:

- O **Mapa da Injustiça Hídrica** compara coleta de esgoto e internações usando medianas dos registros completos. O quadrante é relativo aos municípios observados; correlação visual não demonstra causalidade e os totais SIH continuam em auditoria.
- A **Linha do Tempo** permite inspecionar a co-variação das séries disponíveis (2019–2023), mas não estima impacto causal das obras.
- A **Matriz de Dados** expõe quanto da gestão pública é feita "no escuro", sem informações básicas

---

## 🚧 Dificuldades Enfrentadas

### Coleta de dados:

- **Inconsistência entre fontes**: Dados do SNIS e IBGE usam metodologias diferentes
- **Lacunas temporais**: Muitos municípios simplesmente não reportam dados em certos anos
- **Defasagem**: O CSV atual não contém indicadores de saneamento para 2017, 2018, 2024 e 2025; não há base documentada para tratá-los como projeções.

### Técnicas:

- **Integração de múltiplas fontes**: Unificar SNIS, DATASUS, IBGE e dados climáticos em um único JSON
- **Visualizações responsivas**: Garantir que gráficos complexos funcionem em mobile
- **Performance**: Otimizar carregamento com dados históricos de 9 anos × 7 municípios

### Conceituais:

- **Evitar sensacionalismo**: Apresentar dados críticos sem perder rigor
- **Balancear complexidade**: Dashboard técnico o suficiente para pesquisadores, acessível para cidadãos

---

## 🔮 Melhorias Futuras

### Análises planejadas:

- [ ] **Clima × internações**: explorar a relação temporal entre pluviometria e internações CID-10 A00–A09, após validar cobertura e proveniência dos dois conjuntos de dados
- [ ] **Análise de custo-efetividade**: Quanto cada R$1 em saneamento economiza em internações?
- [ ] **Comparação nacional**: Posicionar a RMB em relação a outras regiões metropolitanas brasileiras
- [ ] **Previsão com ML**: Modelo preditivo de internações baseado em cobertura de saneamento

### Funcionalidades:

- [ ] **Exportar dados**: Botão para download do JSON/CSV filtrado
- [ ] **Modo comparativo**: Selecionar 2 municípios lado a lado
- [ ] **Histórico de atualizações**: Changelog visual de quando dados foram atualizados
- [ ] **API pública**: Endpoint para integração com outros projetos

### Expansão:

- [ ] **Mais municípios**: Incluir toda a área de influência da RMB
- [ ] **Mais indicadores**: Coleta seletiva, tratamento de esgoto, qualidade da água
- [ ] **Séries temporais mais longas**: Dados desde 2010 para análise de longo prazo

---

## 📊 Dados Utilizados

| Fonte             | Dados                                   | Período   |
| ----------------- | --------------------------------------- | --------- |
| **IBGE / FAPESPA** | Estimativas anuais (2017–2021), Censo (2022), referência transportada (2023), estimativas (2024–2025) | 2017–2025 |
| **SNIS**          | Água, Esgoto, Tarifas                   | 2017–2023 |
| **DATASUS (SIH)** | Internações hospitalares por diagnóstico principal CID-10 A00–A09 (doenças intestinais infecciosas; via de transmissão não inferida) | 2017–2025* |
| **INMET**         | Dados climáticos históricos             | 2017-2023 |

* O intervalo é o da série consolidada. A cobertura mensal/anual dos arquivos SIH ainda não foi comprovada; contagens e taxas permanecem em auditoria até que os arquivos de origem sejam conferidos.

*Nota: 2023 repete a população censitária de 2022 como denominador de referência, pois a FAPESPA informa que não houve estimativa municipal do IBGE para 2023. Consulte [a proveniência e as fontes](docs/data-provenance.md).*

### 🏙️ Municípios Monitorados

1. Belém
2. Ananindeua
3. Benevides
4. Castanhal
5. Marituba
6. Santa Bárbara do Pará
7. Santa Izabel do Pará

---

## 🚀 Como Rodar Localmente

### Requisitos

- Navegador web moderno (Chrome, Firefox, Edge)
- Servidor HTTP local (opcional)

### Passos

```bash
# 1. Clone o repositório
git clone https://github.com/enps2015/iara-data-hub.git

# 2. Entre na pasta
cd iara-data-hub

# 3. Inicie um servidor local (escolha uma opção)

# Opção A: Python 3
python -m http.server 8080

# Opção B: Node.js (npx)
npx serve .

# 4. Abra no navegador
# http://localhost:8080
```

---

## 📁 Estrutura do Projeto

```
iara-data-hub/
├── index.html
├── assets/
│   ├── css/styles.css
│   └── js/
│       ├── dataUtils.js    # Leitura, parsing e relatório de qualidade
│       ├── charts.js       # Gráficos e matriz de disponibilidade
│       ├── main.js         # KPIs, cards e detalhes por município
│       └── storytelling.js # Narrativa e apoio à navegação
├── data/iara/
│   └── iara_municipios_rmb.csv
├── img/
├── tests/
│   └── dataUtils.test.cjs
└── .github/workflows/
    └── data-quality.yml    # CI de sintaxe e qualidade dos dados
```

---

## 🧪 Qualidade dos dados e testes

Consulte o [registro de proveniência, cobertura e limitações por indicador](docs/data-provenance.md) antes de interpretar tendências ou reutilizar as séries. A população de 2017–2025 usa fontes documentadas; 2023 é explicitamente identificado como repetição do Censo 2022, não como estimativa independente.

Valores ausentes nos indicadores são preservados como `null` e apresentados como **N/D**. Um zero numérico válido continua sendo zero. O parser não deve preencher lacunas com zero, porque isso distorce médias, rankings e comparações entre municípios.

Ao carregar o CSV, a aplicação registra um resumo de qualidade com contagem de registros, células vazias e valores numéricos inválidos. Registros com formato de CSV inconsistente são rejeitados com uma mensagem explícita, em vez de deslocar silenciosamente os campos.

### Executar os testes locais

Requer Node.js 22 ou compatível com o módulo de testes nativo:

```bash
node --check assets/js/dataUtils.js
node --check assets/js/charts.js
node --check assets/js/main.js
node --test tests/dataUtils.test.cjs
```

O GitHub Actions executa as mesmas verificações em pull requests e em alterações relevantes na aplicação ou no CSV.

## 🔄 Como Atualizar os Dados

Atualize `data/iara/iara_municipios_rmb.csv), mantendo o cabeçalho e uma linha por município/ano. Use o mesmo esquema de colunas do arquivo atual.

- Campo sem informação: deixe vazio; a aplicação exibirá `N/D`.
- Zero conhecido: informe `0`.
- Valor numérico: use ponto como separador decimal.
- Município com vírgula ou aspas: mantenha o campo entre aspas, de acordo com as regras de CSV.

Depois de alterar os dados, execute `node --test tests/dataUtils.test.cjs` e confira o relatório de qualidade no painel. Os gráficos são recalculados a partir dos registros carregados.

---

## 🌐 Deploy no GitHub Pages

### Passos para Publicar

1. Faça push do código para o repositório GitHub
2. Vá em **Settings → Pages**
3. Em "Source", selecione **Deploy from a branch**
4. Escolha a branch `main` e pasta `/ (root)`
5. Clique em **Save**
6. O site estará disponível em: `https://enps2015.github.io/iara-data-hub/`

---

## 🛠️ Tecnologias

- **HTML5 / CSS3** - Estrutura e estilos
- **JavaScript ES6+** - Lógica e interatividade
- **Chart.js** - Gráficos interativos
- **Font Awesome** - Ícones
- **Google Fonts (Outfit)** - Tipografia

---

## 📜 Licença

Este projeto está sob a licença **Creative Commons BY 4.0**.

Uso livre com atribuição ao autor.

---

## 👤 Autor

**Eric Pimentel**  
Engenheiro eletricista e profissional de saneamento, com formação em desenvolvimento de software e especialização em Ciência de Dados em andamento; desenvolve projetos em IA aplicada à sustentabilidade.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ericpimentel-dados/)
[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/enps2015)

---

## 🙏 Agradecimentos

- Instituto I2A2 pela mentoria
- SNIS e DATASUS pelos dados públicos
- Comunidade open-source pelas ferramentas

---

_Desenvolvido com dados públicos e auxílio de ferramentas de Inteligência Artificial._
_© 2025 IARA Data Hub_
