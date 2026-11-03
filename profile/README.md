# Projeto Delta · Monitoramento de consumo de água

![Projeto acadêmico](https://img.shields.io/badge/Projeto-acad%C3%AAmico-2E8B57)
![IoT](https://img.shields.io/badge/IoT-hidr%C3%B4metros-0078D4?logo=arduino&logoColor=white)
![Dados](https://img.shields.io/badge/Dados-PostgreSQL%20%7C%20MongoDB-4169E1?logo=postgresql&logoColor=white)

O Projeto Delta é uma plataforma acadêmica de IoT voltada ao monitoramento residencial do consumo de água. Sensores conectados a hidrômetros coletam medições; os sistemas do projeto organizam esses dados e os apresentam em aplicações e relatórios.

**Tags:** `iot` · `água` · `monitoramento` · `dados` · `postgresql` · `mongodb` · `business-intelligence`

## Frentes do projeto

| Frente | Escopo |
|---|---|
| Medição | Coletar o consumo de água com dispositivos conectados a hidrômetros. |
| Histórico | Organizar as medições e as informações sobre o uso de água da residência. |
| Prevenção | Identificar padrões de consumo e apoiar a investigação de possíveis vazamentos. |
| Planejamento | Estimar gastos e apoiar decisões sobre consumo. |
| Comparação | Explorar metas e rankings de eficiência entre instalações. |
| Contexto | Relacionar o consumo às rotinas da residência e às condições meteorológicas. |
| Acesso | Apresentar informações em dashboards, aplicações e experiências conversacionais. |

## Arquitetura em poucas linhas

- **IoT:** dispositivos como ESP32 e Arduino Uno R4 WiFi coletam pulsos do hidrômetro e transmitem medições.
- **PostgreSQL:** organiza dados relacionais e transacionais, como cadastros e regras de negócio.
- **MongoDB:** armazena dados documentais e telemetria de maior volume.
- **Business Intelligence:** pipelines organizam dados em camadas analíticas para consultas, indicadores e relatórios.

Os bancos, pipelines e aplicações têm repositórios próprios; seus READMEs e documentos técnicos detalham cada componente.

## Explore os repositórios

- [.github](https://github.com/delta-app-ofc/.github)
- [delta-api-mongo](https://github.com/delta-app-ofc/delta-api-mongo)
- [delta-api-postgres](https://github.com/delta-app-ofc/delta-api-postgres)
- [delta-artificial-intelligence](https://github.com/delta-app-ofc/delta-artificial-intelligence)
- [delta-business-intelligence](https://github.com/delta-app-ofc/delta-business-intelligence)
- [delta-business-rules](https://github.com/delta-app-ofc/delta-business-rules)
- [delta-database-primeiroano](https://github.com/delta-app-ofc/delta-database-primeiroano)
- [delta-handbook](https://github.com/delta-app-ofc/delta-handbook)
- [delta-hardware-data-simulator](https://github.com/delta-app-ofc/delta-hardware-data-simulator)
- [delta-ia-observability](https://github.com/delta-app-ofc/delta-ia-observability)
- [delta-landing-page](https://github.com/delta-app-ofc/delta-landing-page)
- [delta-mobile-app](https://github.com/delta-app-ofc/delta-mobile-app)
- [delta-mongo-database](https://github.com/delta-app-ofc/delta-mongo-database)
- [delta-neo4j-database](https://github.com/delta-app-ofc/delta-neo4j-database)
- [delta-redis-database](https://github.com/delta-app-ofc/delta-redis-database)
- [delta-rpa](https://github.com/delta-app-ofc/delta-rpa)
- [delta-servlet](https://github.com/delta-app-ofc/delta-servlet)
- [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database)
- [delta-template-repository](https://github.com/delta-app-ofc/delta-template-repository)
- [delta-web-app](https://github.com/delta-app-ofc/delta-web-app)

## 👥 Integrantes

### 1º Ano
- Bruno Carlos Luz
- Gabriel Ribeiro da Silva
- Lucas Gouveia Paraguassu
- Manuela Dias Velozo
- Pedro Pizzi Conceição
- Pietra Rodrigues Guimarães

### 2º Ano
- Ana Clara Blefari Soares de Souza
- Davi do Nascimento Costa
- João Pedro Araujo de Souza
- Mariana Marrão Ferreira Felis
- Samuel Pimenta Hironimus

---

## ✨ Diferenciais do Projeto

✅ Monitoramento em tempo semi-real com chatbot baseado em dados  
✅ Conversão automática em valor monetário  
✅ Previsão inteligente da conta de água  
✅ Alertas preditivos e detecção automática de vazamentos  
✅ Ranking entre instalações e comparação de padrões  
✅ Arquitetura multi-banco (PostgreSQL, MongoDB, Redis, Neo4j)  
✅ Integração IoT, análise de dados e IA  

---

## 📈 Benefícios Esperados

- Redução do desperdício de água
- Monitoramento contínuo do consumo
- Identificação precoce de vazamentos
- Maior previsibilidade de gastos
- Incentivo ao consumo consciente
- Apoio à tomada de decisão
- Escalabilidade para milhares de dispositivos
