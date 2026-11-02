# Validação Sonar do Delta

## Regras

Apenas achados novos graves afetam merge/aprovacoes: Critical/Blocker no modelo legado ou High/Blocker por impacto. Achados graves antigos da main aparecem somente como divida no comentario; nao bloqueiam a propria PR de correcao. Achados menores nao bloqueiam nem exigem aprovacao extra.

- Todos os testes obrigatórios devem passar (100%). Zero testes não é aprovação.
- Cobertura mínima de 70% somente no código novo/alterado instrumentável.
- Problemas de segurança novos bloqueiam o check `Delta / Política Sonar`.
- Problemas de confiabilidade novos exigem uma aprovação humana além do maior número normal definido por proteção de branch/rulesets.
- Problemas de manutenibilidade aparecem no comentário e não bloqueiam.
- Aprovações precisam ser vigentes, do SHA atual, de pessoas com escrita, diferentes do autor. Comentários não revogam aprovações; dismiss/change request revogam.
- O comentário `delta-sonar-report` é independente do comentário `delta-ci-report` existente. Não altera checkboxes da PR.
- Falta de análise, dados ou configuração nunca é convertida em aprovação.

## Configurar o SonarQube Cloud

1. Entre em <https://sonarcloud.io> com GitHub e importe `delta-app-ofc`.
2. Autorize o aplicativo nos repositórios desejados e importe os projetos com código analisável.
3. Escolha GitHub Actions e desative Automatic Analysis, para usar os relatórios do CI.
4. Confira o plano antes de contratar: há plano Free e OSS para organizações elegíveis, com capacidades diferentes. Não há contratação automática nesta implementação.
5. Cadastre as variáveis Actions `SONAR_ORGANIZATION` e `SONAR_PROJECT_KEY` em cada repo (a segunda é específica por projeto).
6. Cadastre `SONAR_TOKEN` com permissão Execute Analysis. A análise usa somente token Sonar e GitHub somente leitura.
7. Cadastre separadamente `SONAR_POLICY_TOKEN` para a avaliação confiável. A API de contexto do scanner pode exigir administração do projeto; esse token nunca é exposto ao código da PR.
8. Preserve `DELTA_ORG_AUTOMATION_TOKEN` usado pela governança, com leitura das proteções/rulesets, revisões e permissões de colaboradores; escrita em status e comentários. Não cole tokens em arquivos, PRs ou chat.
9. Execute uma análise da branch principal para estabelecer a referência antes de analisar PRs. O fluxo de scan de PR usa explicitamente projeto, número e SHA; o primeiro baseline pode ser disparado pelo tutorial de CI do Sonar.
10. No plano Free não há Quality Gate personalizado. Não torne obrigatório o Quality Gate padrão que bloqueia manutenibilidade/confiabilidade, pois conflita com as regras acima. Torne obrigatório o check próprio Delta, que consulta os achados e cobertura diretamente e verifica o SHA pelo contexto do scanner.

Referências: [onboarding GitHub](https://docs.sonarsource.com/sonarqube-cloud/getting-started/github), [planos](https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans), [API](https://docs.sonarsource.com/sonarqube-cloud/appendices/web-api).

## Workflows e proteção de merge

Os testes executam em `pull_request`, sem tokens administrativos. Geram relatórios, e o job Sonar reutilizável recebe esses artefatos somente após sucesso. Integrações Compose existentes permanecem independentes e obrigatórias.

Os 16 repositórios publicam os mesmos checks: `ci-tecnico` para o gate de testes técnicos e `Testes Sonar` para testes/cobertura ou validação documental/configuração com resumo explícito de N/A nos repositórios sem código analisável. Use o nome exato do job (`jobs.<id>.name`), sem renomear os IDs usados por `needs`. O check de governança conserva o nome composto `validate-pr-checks / Governança da Pull Request`; no `.github`, o workflow local publica esse mesmo nome.

O workflow reutilizável de relatório tenta comentar a PR e atualizar seu corpo de forma independente. Erros nessas publicações geram avisos e resumo na execução; o resultado técnico continua baseado nos jobs necessários, e qualquer job necessário falho, cancelado ou pulado reprova o gate. Se a leitura da PR falhar, nenhum comentário ou marcador de SHA é publicado. Se a atualização do corpo falhar, o marcador de SHA não aparece e a validação local condicionada a esse marcador permanece pulada; os checks obrigatórios `ci-tecnico` e `Testes Sonar` continuam sendo a evidência de aprovação dos testes.

A avaliação roda de código confiável da base por `pull_request_target`/`workflow_run`, sem executar a PR. O workflow sem privilegios de `pull_request_review` sinaliza revisoes novas/removidas; o `workflow_run` reavalia a politica na base confiavel, sem cron. Mudanças de SHA invalidam aprovações antigas. O check será atualizado após a nova análise; consultas concorrentes são rejeitadas para evitar relatório misturado.

Após merge da infraestrutura e teste real da configuração, adicione aos checks obrigatórios da main: o job de testes/cobertura do repo, o job de integração quando aplicável, e `Delta / Política Sonar`. O check de testes técnicos tem o nome `ci-tecnico`; o job de testes e cobertura do fluxo Sonar tem o nome `Testes Sonar`. Preserve os checks/regras atuais e a quantidade normal de revisões. Não aumente globalmente essa quantidade quando só uma PR tem achados. Workflows novos de `workflow_run` precisam existir na branch padrão para operar; esta PR não faz merge automático nem altera CD.

O workflow manual `Ativar checks obrigatórios Sonar` no repo `.github` automatiza esse acréscimo após merge. Informe o repo completo, a branch e um JSON com os nomes exatos dos checks padronizados, como `["ci-tecnico", "Testes Sonar"]`. O workflow acrescenta também `Delta / Política Sonar` e não substitui os checks existentes, revisões, bypasses, permissões ou outras regras. Ele só roda da main e exige proteção já existente. Se a proteção não puder ser lida, não altera nada.

No Free, PRs precisam ter destino main. A branch do RPA deriva de `test/ci-tecnico`, mas a PR tem destino main por decisão do usuário. Commits herdados dessa base aparecem na PR.

Se a proteção/rulesets não puderem ser lidos ou o token Sonar não puder consultar scannerContext, a avaliação permanece pendente/reprovada, com diagnóstico. A ativação e a análise real dependem da configuração externa; testes locais usam respostas sintéticas e não comprovam integração com uma conta Sonar.

## Escopo de cobertura

Não invente percentual para SQL/Cypher ou repositórios só de documentação. Testes de contratos, constraints e queries continuam obrigatórios quando aplicáveis; N/A precisa ser explícito. Scripts Mongo executados por mongosh não ganham cobertura de linhas apenas por um smoke passar. Os relatórios de Python/Java/JavaScript devem incluir o código real, e não somente os arquivos importados pelos testes.

Security Hotspots são pontos que exigem triagem humana, não equivalem automaticamente a vulnerabilidades confirmadas. Sua triagem deve ser configurada no Quality Gate quando adotada; a política de achados classifica vulnerabilidades/impacts de segurança retornados pelo endpoint de issues.

O delta-sql-database tambem instrumenta bi_etl.py. Ao ativar seus checks, inclua os testes Python e o smoke PostgreSQL. Os arquivos SQL continuam validados por comportamento, sem percentual de linhas SQL.

O workflow tambem analisa push na main, depois dos testes, para atualizar a referencia e a divida historica. A analise da main nao envia parametros de pull request. A primeira referencia pode ser disparada manualmente na main apos o merge dos workflows.
