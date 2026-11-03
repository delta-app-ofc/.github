# Delta · Automação de Pull Requests no GitHub

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-workflows-2088FF?logo=githubactions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Governança](https://img.shields.io/badge/PRs-checks%20e%20roteamento-2E8B57)

Este repositório reúne workflows e scripts compartilhados para validar Pull Requests, encaminhar revisões e registrar verificações técnicas dos repositórios Delta. Também contém o perfil público da organização e o template de PR.

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
| Workflow reutilizável | Valida commits, `.gitignore` e o corpo da PR; encaminha revisões conforme o escopo marcado. |
| Scripts Python | Validam commits, arquivos ignorados, checklist, bypass e roteamento de revisores. |
| Testes | Cobrem scripts, contratos e arquivos YAML com a suíte `unittest`. |
| Workflows de qualidade | Executam testes, registram resultados na PR e apoiam análise e política Sonar. |
| Perfil público e template | Apresentam o Projeto Delta e fornecem o modelo de Pull Request da organização. |

O workflow `report_ci.yml` atualiza o status e o checkbox de testes da PR após a conclusão dos jobs técnicos.

## Estrutura do repositório

| Caminho | Conteúdo |
|---|---|
| `.github/workflows/main.yml` | Workflow reutilizável de governança chamado pelos repositórios da organização. |
| `.github/workflows/local_checks.yml` | Governança de Pull Requests deste repositório. |
| `.github/workflows/test.yml` | Testes técnicos com Python 3.12 e publicação do resultado na PR. |
| `.github/workflows/report_ci.yml` | Resume os jobs técnicos e registra o resultado da PR. |
| `.github/workflows/sonar*.yml` | Workflows de análise Sonar, configuração de checks e política de revisão. |
| `scripts/` | Validadores de commits, `.gitignore`, bypass, checklist e revisores, além da política Sonar. |
| `tests/` | Testes unitários e de contratos dos scripts e workflows. |
| `profile/README.md` | Apresentação pública da organização no GitHub. |
| `pull_request_template.md` | Template compartilhado de Pull Request. |
| `requirements-dev.txt` | Dependências de desenvolvimento e teste. |

## Como funciona a governança de PR

1. O repositório consumidor chama `delta-app-ofc/.github/.github/workflows/main.yml`.
2. O workflow consulta o bypass emergencial e valida commits, `.gitignore` e o corpo da PR.
3. `route_checks.py` confere escopo, tipo de PR, itens obrigatórios, declaração de uso de IA e descrição.
4. `route_reviewers.py` associa os módulos marcados aos times da organização e solicita revisão pela GitHub CLI.
5. O workflow técnico do repositório consumidor executa seus testes e pode chamar `report_ci.yml` para registrar o resultado na PR.

Nos Pull Requests deste repositório, `local_checks.yml` executa as verificações de governança. Os demais workflows atendem testes e integração de qualidade; consulte `.github/workflows/` ao alterar eventos, permissões ou segredos.

## Desenvolvimento e testes locais

Requer Python 3.12. Na raiz deste repositório, instale as dependências e rode as verificações:

```bash
python -m pip install -r requirements-dev.txt
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
```

Os testes locais rodam sem token da organização. Os workflows que interagem com Pull Requests ou APIs do GitHub usam credenciais configuradas no GitHub Actions.

## Configuração e segurança

- Configure `GH_TOKEN` e os demais segredos de automação nos workflows que os utilizam.
- Defina as permissões dos workflows de acordo com as operações realizadas em Pull Requests e APIs do GitHub.
- Mantenha tokens fora de scripts, arquivos de configuração, exemplos e logs.
- Preserve os textos dos checkboxes usados pelo template, pelos scripts de roteamento e pela validação da PR.

## Repositórios relacionados

- [delta-handbook](https://github.com/delta-app-ofc/delta-handbook): convenções de desenvolvimento e documentação do processo de PR.
- [Organização delta-app-ofc](https://github.com/delta-app-ofc): repositórios que usam as automações compartilhadas.
