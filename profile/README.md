# Projeto Delta - Sistema Inteligente de Monitoramento e Gestão do Consumo de Água

Plataforma IoT completa para monitoramento inteligente do consumo de água residencial, com detecção de vazamentos, previsão de gastos e análise comportamental em tempo semi-real.

---

## 📋 Essência do Projeto

O Projeto Delta surge como uma solução tecnológica inovadora para o monitoramento inteligente do consumo de água em residências. Utilizando dispositivos IoT instalados em hidrômetros, a plataforma coleta dados de consumo, processa-os em tempo semi-real e disponibiliza informações relevantes através de uma plataforma web e mobile. Além do monitoramento, o sistema emprega análise de dados e inteligência artificial para identificar vazamentos, gerar alertas preditivos, prever gastos futuros e auxiliar na redução do desperdício de água, contribuindo para a preservação de recursos hídricos e redução de custos.

---

## 🎯 Funcionalidades Principais

- **Monitoramento em Tempo Semi-Real**: Acompanhamento do consumo em intervalos configuráveis (5, 10 ou 15 minutos) com visualização de consumo acumulado, vazão média e evolução temporal
- **Conversão Automática em Valor Monetário**: Conversão do consumo em estimativa financeira baseada nas tarifas cadastradas da concessionária
- **Alertas Inteligentes**: Notificações quando o consumo ultrapassa limites definidos ou foge do padrão esperado, com alertas preditivos sobre ultrapassagem de metas
- **Detecção Automática de Vazamentos**: Análise contínua do fluxo de água para identificar possíveis vazamentos
- **Chatbot Inteligente**: Consultas em linguagem natural sobre dados da residência ("Quanto consumi hoje?", "Existe vazamento?", "Quanto vou pagar?")
- **Metas de Consumo**: Definição de limites em litros, metros cúbicos ou valor monetário para controle proativo
- **Ranking e Comparação**: Comparação entre instalações por consumo total, consumo per capita e economia mensal
- **Cadastro de Rotina**: Personalização com características da residência para melhorar precisão dos algoritmos
- **Previsão da Conta de Água**: Estimativa do valor da próxima fatura baseada em consumo atual e histórico
- **Dashboard Gerencial**: Painel central com consumo diário/semanal/mensal, evolução histórica, alertas ativos e ranking
- **Integração com API do Tempo**: Informações meteorológicas em tempo real para apoio à tomada de decisão diária

---

## 🏗️ Arquitetura da Solução

### Camada IoT
- **Sensor Hall**: Acoplado ao hidrômetro
- **ESP32**: Processamento local e transmissão via Wi-Fi
- **Dados Coletados**: Device ID, data/hora, quantidade de pulsos, vazão instantânea, consumo calculado

### Fluxo de Dados
Sensor Hall → ESP32 → API REST → MongoDB → Processamento → PostgreSQL → Redis → Web/Mobile

### Componentes de Armazenamento
- **MongoDB**: Armazenamento de eventos de sensores
- **PostgreSQL**: Dados estruturados de usuários e configurações
- **Redis**: Cache e processamento em tempo real
- **Neo4j**: Análise de relacionamentos entre dados

---

## 📁 Estrutura do Repositório



---

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
- Rahquel Korzh Emidio
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