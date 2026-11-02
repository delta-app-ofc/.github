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

teams_to_add = (
    set()
)  # set para não haver repetição de times caso haja mais de um checkbox marcado para o mesmo time
results = []

# Varre o corpo do PR procurando os termos (ignorando maiúsculas/minúsculas)
for key, team in mapping.items():
    if key.lower() in pr_body.lower():
        teams_to_add.add(team)

# Executa o comando da GitHub CLI para cada time encontrado
for team in teams_to_add:
    full_team_name = f"{org_name}/{team}"
    print(f"Solicitando revisão do time: {full_team_name}")

    # Chama a ferramenta 'gh' do sistema
    try:
        result = subprocess.run(
            ["gh", "pr", "edit", pr_url, "--add-reviewer", full_team_name],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        print(f"::warning::Não foi possível solicitar revisão para {full_team_name} ({type(error).__name__}).")
        results.append(f"- {full_team_name}: solicitação não executada ({type(error).__name__}).")
        continue

    if result.returncode:
        print(f"::warning::Não foi possível solicitar revisão para {full_team_name} (código {result.returncode}).")
        results.append(f"- {full_team_name}: solicitação falhou (código {result.returncode}).")
    else:
        results.append(f"- {full_team_name}: revisão solicitada.")

summary_path = os.getenv("GITHUB_STEP_SUMMARY")
if summary_path:
    summary = "## Roteamento de revisores\n\n" + (
        "\n".join(results) if results else "Nenhum time de revisão selecionado."
    ) + "\n"
    try:
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write(summary)
    except OSError as error:
        print(f"::warning::Não foi possível gravar o resumo de revisores ({type(error).__name__}).")
