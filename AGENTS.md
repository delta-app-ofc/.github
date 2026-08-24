# AGENTS.md — Contexto do repositório `.github` do Projeto Delta

Este arquivo orienta agentes de IA e pessoas desenvolvedoras que atuem neste repositório. Antes de alterar qualquer arquivo, confirme o estado atual da branch, leia as instruções locais e valide o conteúdo real do repositório. Não presuma que componentes documentados em outros repositórios já estejam implementados aqui.

## 1. Visão geral do Projeto Delta

O Projeto Delta é uma plataforma acadêmica de monitoramento inteligente do consumo de água residencial. Dispositivos IoT instalados em hidrômetros coletam pulsos e enviam dados para uma arquitetura que pretende consolidar consumo, detectar vazamentos, prever gastos e disponibilizar informações em aplicações web e mobile, além de um chatbot.

A organização `delta-app-ofc` mantém repositórios independentes para documentação, bancos de dados e demais partes da solução. PostgreSQL é destinado aos dados cadastrais e transacionais, enquanto MongoDB atende telemetria e dados de alto volume. Redis e Neo4j aparecem na documentação de arquitetura como componentes planejados; este repositório não contém implementação desses bancos nem código das aplicações de negócio.

## 2. Contexto deste repositório

Este é o repositório especial `delta-app-ofc/.github`. Seu papel é centralizar arquivos de governança e automações compartilhadas pela organização no GitHub. Ele não é o backend, o frontend nem um repositório de banco de dados do produto.

As tecnologias efetivamente usadas aqui são Markdown, YAML para GitHub Actions e Python. O comando `gh pr edit` é chamado pelo script de roteamento no ambiente do workflow.

### Estrutura atual

```text
.
├── .github/
│   └── workflows/
│       ├── local_checks.yml
│       └── main.yml
├── profile/
│   └── README.md
├── scripts/
│   ├── route_checks.py
│   └── route_reviewers.py
├── .gitignore
├── LICENSE
└── pull_request_template.md
```

Responsabilidades dos arquivos principais:

- `profile/README.md`: apresenta publicamente o Projeto Delta na página da organização.
- `pull_request_template.md`: define o template padrão de Pull Request compartilhado pela organização.
- `scripts/route_checks.py`: valida módulo impactado, tipo de PR, declaração de uso de IA, checks obrigatórios e descrição útil do Pull Request.
- `scripts/route_reviewers.py`: relaciona os módulos marcados no template aos times responsáveis e solicita revisores com a GitHub CLI.
- `.github/workflows/main.yml`: workflow reutilizável, acionado por `workflow_call`, que executa as validações e o roteamento para repositórios consumidores.
- `.github/workflows/local_checks.yml`: executa o mesmo fluxo em Pull Requests deste próprio repositório.

Alterações nesses arquivos podem afetar a governança de Pull Requests de vários repositórios. Preserve a compatibilidade entre os textos dos checkboxes do template, as comparações feitas nos scripts e os eventos, segredos e permissões configurados nos workflows.

## 3. Leitura obrigatória do `TASK.md`

Antes de executar qualquer tarefa, leia integralmente o arquivo `TASK.md` da raiz deste repositório, quando ele estiver presente, e trate seus critérios de aceite e limitações como parte obrigatória do escopo.

Não crie, copie ou improvise um `TASK.md`. Se ele não existir, trabalhe somente a partir da tarefa fornecida explicitamente e solicite esclarecimento quando o escopo não puder ser determinado com segurança.

## 4. Padrão de branches e commits

Siga as convenções mantidas em `delta-handbook/DEVOPS/convencoes-desenvolvimento.md`.

O nome de uma branch deve seguir:

```text
<tipo>/<descricao-da-alteracao>
```

Tipos permitidos:

| Tipo | Uso |
| --- | --- |
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração |
| `docs` | Alteração de documentação |
| `test` | Criação ou manutenção de testes |
| `style` | Alteração de estilização |

Use uma descrição curta e identificável, como `docs/agents-md`. Crie a branch no próprio repositório `.github`, sempre a partir da `main` atualizada. Não inicialize Git na pasta que apenas agrupa os repositórios locais do Delta.

Os commits seguem Conventional Commits no formato `<tipo>: descrição`, usando os mesmos tipos permitidos para branches. Mantenha commits objetivos, de escopo coeso e com mensagem que explique a alteração.

## 5. Padrão de documentação

Ao criar ou atualizar Markdown, acompanhe o padrão observado no `delta-handbook`:

- comece com um título principal claro usando `#`;
- apresente objetivo e contexto antes dos detalhes operacionais;
- organize o conteúdo em seções `##` e subseções `###`, com ordem lógica;
- use listas para responsabilidades, regras e passos, sem transformar parágrafos curtos em estruturas desnecessárias;
- use tabelas quando houver comparação ou mapeamento de campos;
- destaque nomes de arquivos, caminhos, branches, comandos e identificadores com crases;
- identifique a linguagem em blocos de código, como `text`, `yaml`, `python` ou `markdown`;
- use separadores horizontais apenas quando ajudarem a dividir blocos extensos;
- escreva em português claro, objetivo e tecnicamente correto;
- mantenha termos técnicos, nomes de arquivos e comportamento descrito alinhados ao conteúdo real do repositório;
- atualize exemplos e referências relacionadas quando uma mudança tornar a documentação anterior incorreta.

Para documentos de governança de Pull Requests, preserve a correspondência literal necessária entre o template, os scripts de validação e roteamento e a documentação do handbook.

## 6. Limites de atuação

- Não invente aplicações, serviços, dependências, workflows ou estruturas que não existam no repositório.
- Não altere código de produto ou arquivos de outros repositórios sem que a tarefa os inclua explicitamente.
- Não trate Redis ou Neo4j como implementados neste repositório.
- Não exponha tokens, segredos ou valores de credenciais em documentação, scripts ou logs.
- Restrinja cada alteração ao escopo definido no `TASK.md` ou na solicitação explícita recebida.

## 7. Limite de complexidade e nível técnico

As soluções devem ser compatíveis com o conhecimento de estudantes do Ensino Médio Técnico em Análise e Desenvolvimento de Sistemas.

- Priorize código simples, legível e dividido em pequenas responsabilidades.
- Utilize primeiro os recursos já presentes no repositório e conhecidos pela equipe.
- Não adicione frameworks, bibliotecas, padrões arquiteturais ou infraestrutura sem necessidade comprovada.
- Evite abstrações prematuras, metaprogramação, arquiteturas distribuídas e padrões avançados quando uma solução direta atender ao requisito.
- Não reestruture grandes partes do projeto para resolver uma tarefa localizada.
- Explique decisões técnicas e trechos não óbvios com linguagem didática.
- Quando a solução exigir conhecimento acima do limite registrado abaixo, apresente primeiro uma alternativa mais simples e solicite aprovação antes de prosseguir.
- Não implemente automaticamente uma solução avançada sem justificativa e autorização explícita.

### Stack e nível de aprofundamento da equipe

| Tecnologia ou assunto | Nível atual | Limite esperado |
| --- | --- | --- |
| Lógica de programação | Intermediário | Avançado |
| Git e GitHub | Intermediário | Avançado |
| HTML e CSS | Básico | Intermediário |
| JavaScript | Básico | Intermediário |
| Java | Intermediário | Avançado |
| Spring Boot | Básico | Avançado |
| Python | Intermediário | Avançado |
| FastAPI | Básico | Intermediário |
| SQL e PostgreSQL | Avançado | Avançado |
| MongoDB | Básico | Intermediário |
| APIs REST | Intermediário | Intermediário |
| Testes automatizados | Básico | Intermediário |
| Docker e CI/CD | Básico | Intermediário |
| Arquitetura e padrões de projeto | Básico | Intermediário |
| IoT e comunicação com hardware | Básico | Básico |

O **nível atual** representa o conhecimento que a equipe já possui e consegue aplicar com alguma autonomia. O **limite esperado** representa o nível máximo de complexidade que a IA pode utilizar.

Quando o limite esperado for superior ao nível atual, a IA deve explicar os novos conceitos de forma simples e didática, relacionando-os ao código produzido. Qualquer solução que ultrapasse o limite esperado exige aprovação explícita antes da implementação.

## 8. Aviso de manutenção

A seção **Estrutura atual do repositório** deve ser revisada periodicamente nesta conversa e atualizada depois
de commits oficiais que adicionem, removam ou reorganizem arquivos. Antes de cada atualização, compare esta
descrição com a árvore real da `main`; o conteúdo deste arquivo não substitui a inspeção do estado atual.
