"""Autoriza bypass de governança apenas para a label aplicada por Samuel."""

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

BYPASS_LABEL = "ci-bypass"
AUTHORIZED_LOGIN = "samuelpimentah"


def github_get(path: str):
    """Consulta a API autenticada; erros impedem o bypass (fail closed)."""
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    request = Request(
        f"{api_url}/{path}",
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def authorized_label_actor(events: list[dict]) -> bool:
    """Exige que a última alteração desta label seja a aplicação por Samuel."""
    relevant = [
        event
        for event in events
        if event.get("event") in {"labeled", "unlabeled"}
        and event.get("label", {}).get("name") == BYPASS_LABEL
    ]
    if not relevant:
        return False
    latest = relevant[-1]
    return (
        latest["event"] == "labeled"
        and (latest.get("actor") or {}).get("login", "").lower()
        == AUTHORIZED_LOGIN
        and not latest.get("performed_via_github_app")
    )


def github_paginate(path: str) -> list[dict]:
    """Lê todas as páginas para não perder uma aplicação recente da label."""
    items = []
    page = 1
    while True:
        batch = github_get(f"{path}?per_page=100&page={page}")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text("utf-8"))
    pr_number = event["pull_request"]["number"]
    repository = os.environ["GITHUB_REPOSITORY"]
    prefix = f"repos/{repository}/issues/{pr_number}"
    labels = github_paginate(f"{prefix}/labels")
    bypass = False
    if any(label["name"] == BYPASS_LABEL for label in labels):
        events = github_paginate(f"{prefix}/timeline")
        bypass = authorized_label_actor(events)
        if not bypass:
            print("::warning::ci-bypass não autorizado; as validações serão executadas.")

    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as output:
        output.write(f"enabled={str(bypass).lower()}\n")
    if bypass:
        message = (
            f"Bypass emergencial autorizado por @{AUTHORIZED_LOGIN} na PR #{pr_number}. "
            "As validações de commits, .gitignore e checklist não foram executadas. "
            "Nenhum checkbox será marcado automaticamente. "
            "Remova ci-bypass para reativar as validações."
        )
        print(f"::warning::{message}")
        with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as summary:
            summary.write(f"## Bypass emergencial de CI\n\n{message}\n")
    else:
        print("Bypass desativado; validações normais mantidas.")


if __name__ == "__main__":
    main()
