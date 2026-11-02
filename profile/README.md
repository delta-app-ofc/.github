# Projeto Delta · Monitoramento inteligente de água

![Projeto acadêmico](https://img.shields.io/badge/Projeto-acad%C3%AAmico-2E8B57)
![IoT](https://img.shields.io/badge/IoT-hidr%C3%B4metros-0078D4?logo=arduino&logoColor=white)
![Dados](https://img.shields.io/badge/Dados-PostgreSQL%20%7C%20MongoDB-4169E1?logo=postgresql&logoColor=white)

Cada pulso do hidrômetro conta uma história. O Projeto Delta transforma medições de consumo de água em dados que ajudam a entender hábitos, acompanhar gastos e investigar sinais de desperdício.

O Delta é um projeto acadêmico de uma plataforma IoT para monitoramento residencial de água. Sensores conectados a hidrômetros coletam medições; os sistemas do projeto organizam esses dados e os apresentam em aplicações e relatórios. A equipe trabalha em repositórios independentes para código, bancos de dados, documentação e análise.

**Tags:** `iot` · `água` · `monitoramento` · `dados` · `postgresql` · `mongodb` · `business-intelligence`

## O que o projeto busca oferecer

| Frente | Objetivo |
|---|---|
| Medição | Acompanhar o consumo a partir de dispositivos conectados a hidrômetros. |
| Compreensão | Organizar histórico e informações sobre o uso de água da residência. |
| Prevenção | Apoiar a identificação de consumo fora do padrão e a investigação de possíveis vazamentos. |
| Planejamento | Ajudar a estimar gastos e tomar decisões com mais contexto. |
| Metas e comparação | Explorar limites de consumo, rankings e comparação entre instalações. |
| Contexto da residência | Considerar rotinas e informações meteorológicas na leitura do consumo. |
| Acesso | Reunir informações em dashboards, aplicações e experiências conversacionais do projeto. |

Essas frentes descrevem o propósito do Delta; a disponibilidade de cada recurso depende do estado do componente correspondente. Consulte os repositórios e documentos técnicos para distinguir o que já está implementado do que ainda está em evolução.

## Arquitetura em poucas linhas

- **IoT:** dispositivos como ESP32 e Arduino Uno R4 WiFi podem coletar os pulsos do hidrômetro e transmitir medições.
- **PostgreSQL:** organiza dados relacionais e transacionais, como cadastros e regras de negócio.
- **MongoDB:** atende dados documentais e telemetria de maior volume.
- **Análise:** os pipelines de Business Intelligence transformam dados em camadas analíticas e relatórios.

Os bancos e aplicações vivem em repositórios separados. A arquitetura evolui junto com os componentes; este perfil não afirma que todo fluxo esteja implantado ou conectado em produção.

## Explore os repositórios

- [delta-handbook](https://github.com/delta-app-ofc/delta-handbook) — arquitetura, regras de negócio e documentação do projeto.
- [delta-sql-database](https://github.com/delta-app-ofc/delta-sql-database) — scripts e estruturas relacionais do PostgreSQL.
- [delta-mongo-database](https://github.com/delta-app-ofc/delta-mongo-database) — coleções e configuração do MongoDB.
- [delta-business-intelligence](https://github.com/delta-app-ofc/delta-business-intelligence) — pipelines e consultas analíticas.
- [delta-app-ofc](https://github.com/delta-app-ofc) — demais repositórios da organização.

## Construído em equipe

O Delta é desenvolvido por estudantes e reúne conhecimentos de IoT, engenharia de software, bancos de dados, análise de dados e experiência do usuário. A documentação de cada repositório é o melhor ponto de partida para entender sua estrutura e contribuir.
