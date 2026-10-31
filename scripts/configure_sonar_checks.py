"""Adiciona checks obrigatórios sem substituir as demais proteções da branch.

Uso após merge e validação real do onboarding Sonar, pelo workflow manual.
Não cria uma proteção nova com defaults que poderiam apagar regras da equipe.
"""
import json
import os
from urllib.parse import quote
from scripts.sonar_policy import API, CHECK


def configure(api, repo, branch, extra_checks):
    if not repo.startswith("delta-app-ofc/"):
        raise ValueError("Repositório fora da organização Delta")
    if not all(isinstance(name, str) and name.strip() for name in extra_checks):
        raise ValueError("Nomes dos checks devem ser textos não vazios")
    path = f"/repos/{repo}/branches/{quote(branch, safe='')}/protection"
    protection = api.call(path)
    original = protection.get("required_status_checks") or {}
    checks = [dict(item) for item in original.get("checks", [])]
    # GitHub antigo pode devolver somente contexts. Não perde esses checks.
    for name in original.get("contexts", []):
        if not any(check["context"] == name for check in checks):
            checks.append({"context": name})
    for name in [CHECK, *extra_checks]:
        if not any(check["context"] == name for check in checks):
            checks.append({"context": name})
    return api.call(path + "/required_status_checks", "PATCH", {
        "strict": original.get("strict", True), "checks": checks})


if __name__ == "__main__":
    configure(API("https://api.github.com", os.environ["GH_TOKEN"]),
              os.environ["TARGET_REPOSITORY"], os.environ.get("TARGET_BRANCH", "main"),
              json.loads(os.environ["REQUIRED_TEST_CHECKS"]))
    print("Checks acrescentados; demais regras da branch foram preservadas.")
