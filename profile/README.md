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

- [delta-handbook](https://github.com/delta-app-ofc/delta-handbook) — arquitetura, regras de negócio e documentação do projeto.
- [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database) — scripts e estruturas relacionais do PostgreSQL.
- [delta-mongo-database](https://github.com/delta-app-ofc/delta-mongo-database) — coleções e configuração do MongoDB.
- [delta-business-intelligence](https://github.com/delta-app-ofc/delta-business-intelligence) — pipelines e consultas analíticas.
- [delta-app-ofc](https://github.com/delta-app-ofc) — demais repositórios da organização.

## Construído em equipe

O Delta é desenvolvido por estudantes e reúne conhecimentos de IoT, engenharia de software, bancos de dados, análise de dados e experiência do usuário. A documentação dos repositórios apresenta a estrutura e as formas de contribuição de cada área.
