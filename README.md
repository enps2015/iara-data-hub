# 🌊 IARA Data Hub

**Indicadores de Água, Resiliência e Adaptação – Região Metropolitana de Belém**

![IARA Data Hub Cover](img/iara_cover.png)

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

> **"O que esses investimentos significam para quem ainda convive com esgoto a céu aberto, água intermitente e doenças 100% evitáveis?"**

Como profissional de dados e morador da Amazônia, percebi que **os dados existiam, mas estavam dispersos**. O SNIS tem informações sobre saneamento, o DATASUS sobre internações, o IBGE sobre população — mas ninguém estava conectando esses pontos para contar a história completa.

O IARA nasceu dessa necessidade: **um observatório crítico que não repete discursos oficiais, mas mostra a distância entre promessa e realidade através de dados.**

---

## 🔍 O Que Este Projeto Demonstra

### Correlações importantes:

- **Saneamento × Saúde**: Municípios com menor cobertura de esgoto apresentam maiores taxas de internações por doenças hídricas
- **Apagão de Dados**: A série de 2017–2025 contém lacunas importantes. Em 2023, três dos sete municípios não têm coleta de esgoto informada; gráficos que relacionam saneamento e internações usam somente registros com ambos os indicadores disponíveis.
- **Desigualdade Metropolitana**: Enquanto alguns municípios avançam, outros permanecem na "zona crítica" do mapa da injustiça hídrica

### Insights visuais:

- O **Mapa da Injustiça Hídrica** compara coleta de esgoto e internações usando medianas dos registros completos. O quadrante mais favorável é relativo aos municípios observados e não significa, por si só, que a situação sanitária seja ideal em termos absolutos.
- A **Linha do Tempo** revela se a aceleração de obras (2019-2023) impactou a curva de internações
- A **Matriz de Dados** expõe quanto da gestão pública é feita "no escuro", sem informações básicas

---

## 🚧 Dificuldades Enfrentadas

### Coleta de dados:

- **Inconsistência entre fontes**: Dados do SNIS e IBGE usam metodologias diferentes
- **Lacunas temporais**: Muitos municípios simplesmente não reportam dados em certos anos
- **Defasagem**: Dados de saneamento mais recentes são de 2023; 2024-2025 ainda são projeções

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

- [ ] **Correlação clima × internações**: Cruzar dados de pluviometria com picos de doenças hídricas
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
| **IBGE**          | População (Censo 2022 + Estimativas)    | 2017-2025 |
| **SNIS/SINISA**   | Água, Esgoto, Tarifas                   | 2017-2023 |
| **DATASUS (SIH)** | Internações hospitalares (CIDs A00-A09) | 2017-2025 |
| **INMET**         | Dados climáticos históricos             | 2017-2023 |

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
6. O site estará disponível em: `https://seu-usuario.github.io/iara-data-hub/`

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
Engenheiro, Cientista de Dados e pesquisador em Inteligência Artificial aplicada à Sustentabilidade.

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
