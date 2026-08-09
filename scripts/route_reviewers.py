import os
import subprocess

pr_body = os.getenv("PR_BODY", "")
pr_url = os.getenv("PR_URL", "")
org_name = os.getenv("ORG_NAME", "")

# Mapeamento dos checkboxes para os respectivos times
mapping = {
    "- [x] Backend (Java / Servlets / DAO)": "backend-1ano",
    "- [x] Frontend (HTML / CSS / Landing Page)": "frontend-1ano",
    "- [x] Database (Modelo Lógico / Script SQL)": "dados-1ano",
    "- [x] Planilha de Controle / SO": "gestao-1ano",
    "- [x] API REST (Spring Boot)": "backend-2ano",
    "- [x] Aplicação Dinâmica (React / TypeScript)": "frontend-2ano",
    "- [x] Mobile (Android / iOS / Firebase)": "backend-2ano",
    "- [x] IA Multiagente (FastAPI / Langgraph)": "dados-2ano",
    "- [x] Banco de Dados (Postgres, MongoDB, Redis ou Neo4J)": "dados-2ano",
    "- [x] Infraestrutura / Pipeline de CI/CD": "gestao-2ano",
    "- [x] Gestão de projetos / Documentação / UX": "gestao-2ano",
}

teams_to_add = set() # set para não haver repetição de times caso haja mais de um checkbox marcado para o mesmo time

# Varre o corpo do PR procurando os termos (ignorando maiúsculas/minúsculas)
for key, team in mapping.items():
    if key.lower() in pr_body.lower():
        teams_to_add.add(team)

# Executa o comando da GitHub CLI para cada time encontrado
for team in teams_to_add:
    full_team_name = f"{org_name}/{team}"
    print(f"Solicitando revisão do time: {full_team_name}")

    # Chama a ferramenta 'gh' do sistema
    subprocess.run(["gh", "pr", "edit", pr_url, "--add-reviewer", full_team_name])