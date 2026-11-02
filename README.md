# Delta · Automação e governança no GitHub

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-workflows-2088FF?logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Governança](https://img.shields.io/badge/PRs-checks%20e%20roteamento-2E8B57)

Este repositório mantém as regras compartilhadas que fazem uma Pull Request do Delta passar por verificações consistentes e chegar às pessoas revisoras certas. Ele concentra workflows reutilizáveis, validação de PR, roteamento de times e políticas de qualidade; não contém código das aplicações do produto.

**Tags:** `github-actions` · `governança` · `pull-request` · `python` · `ci` · `sonar`

## Sumário

- [Visão geral](#visão-geral)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como funciona a governança de PR](#como-funciona-a-governança-de-pr)
- [Desenvolvimento e testes locais](#desenvolvimento-e-testes-locais)
- [Configuração e segurança](#configuração-e-segurança)
- [Repositórios relacionados](#repositórios-relacionados)

## Visão geral

| Parte | Responsabilidade |
|---|---|
| Workflow reutilizável | Valida commits e `.gitignore`, verifica o preenchimento da PR e solicita revisores com base no escopo marcado. |
| Scripts Python | Implementam as validações de commits, arquivos ignorados, conteúdo da PR, bypass controlado e roteamento. |
| Testes | Conferem scripts, contratos e arquivos YAML com a suíte `unittest`. |
| Workflows de qualidade | Executam testes, reportam o resultado na PR e apoiam análise e política Sonar. |
| Perfil público e template | Apresentam o Projeto Delta e fornecem o modelo de Pull Request da organização. |

O checkbox de testes da PR é atualizado pelo workflow de CI quando os jobs técnicos terminam; a validação do texto da PR, por si só, não substitui essa execução.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `.github/workflows/main.yml` | Workflow reutilizável de governança chamado pelos repositórios da organização. |
| `.github/workflows/local_checks.yml` | Fluxo de governança de PR deste próprio repositório. |
| `.github/workflows/test.yml` | Testes técnicos com Python 3.12 e publicação do resultado na PR. |
| `.github/workflows/report_ci.yml` | Workflow reutilizável que resume os jobs técnicos e registra o resultado da PR. |
| `.github/workflows/sonar*.yml` | Workflows de análise Sonar, configuração de checks e política de revisão. |
| `scripts/` | Validadores de commits, `.gitignore`, bypass, checklist e roteamento de revisores, além da política Sonar. |
| `tests/` | Testes unitários e de contratos dos scripts e workflows. |
| `profile/README.md` | Apresentação pública da organização no GitHub. |
| `pull_request_template.md` | Template compartilhado de Pull Request. |
| `requirements-dev.txt` | Dependências de desenvolvimento e teste. |

## Como funciona a governança de PR

1. O repositório consumidor chama `delta-app-ofc/.github/.github/workflows/main.yml`.
2. O workflow verifica se há um bypass emergencial válido e, quando não há, valida commits, `.gitignore` e o corpo da PR.
3. `route_checks.py` confere escopo, tipo de PR, itens obrigatórios, declaração de uso de IA e uma descrição útil.
4. `route_reviewers.py` associa os módulos marcados aos times da organização e solicita revisão pela GitHub CLI.
5. O workflow técnico do repositório consumidor executa seus testes e pode chamar `report_ci.yml` para registrar o resultado na própria PR.

Nos Pull Requests do próprio `.github`, `local_checks.yml` executa as verificações locais. Os outros workflows atendem testes e integração de qualidade; consulte os arquivos em `.github/workflows/` antes de alterar eventos, permissões ou segredos.

## Desenvolvimento e testes locais

Requer Python 3.12 para reproduzir a versão usada pelo workflow de testes. A partir da raiz deste repositório:

```bash
python -m pip install -r requirements-dev.txt
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
```

O workflow executa a mesma instalação, verificação de sintaxe e suíte unitária. Os testes não precisam de token da organização; credenciais só são necessárias nos workflows que interagem com PRs ou APIs do GitHub.

## Configuração e segurança

- O workflow reutilizável recebe `GH_TOKEN`; os consumidores configuram o segredo de automação da organização conforme o próprio workflow.
- Os fluxos escrevem em PRs e solicitam revisores, portanto suas permissões e segredos devem permanecer limitados ao necessário.
- Nunca grave tokens em scripts, arquivos de configuração, exemplos ou logs.
- Preserve os textos dos checkboxes usados pelo template, pelos scripts de roteamento e pela validação da PR. Uma mudança em apenas um desses pontos pode quebrar o fluxo dos repositórios consumidores.

## Repositórios relacionados

- [delta-handbook](https://github.com/delta-app-ofc/delta-handbook): convenções de desenvolvimento e documentação do processo de PR.
- [Organização delta-app-ofc](https://github.com/delta-app-ofc): repositórios que consomem as automações compartilhadas.
