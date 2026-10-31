"""Política Delta: segurança bloqueia, confiabilidade exige revisão adicional.

Executar somente por workflow confiável da branch base, sem executar código da PR.
As APIs são injetáveis para permitir testes sem tokens ou chamadas externas.
"""

import json
import os
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


CHECK = "Delta / Política Sonar"
MARKER = "<!-- delta-sonar-report -->"


def grave_counts(issues):
    """HIGH/BLOCKER por impacto; CRITICAL/BLOCKER no modelo legado."""
    counts = {"SECURITY": 0, "RELIABILITY": 0, "MAINTAINABILITY": 0}
    legacy = {"VULNERABILITY": "SECURITY", "BUG": "RELIABILITY", "CODE_SMELL": "MAINTAINABILITY"}
    for issue in issues:
        if issue.get("status") in {"CLOSED", "RESOLVED"} or issue.get("resolution"):
            continue
        impacts = issue.get("impacts", [])
        if impacts:
            qualities = {impact["softwareQuality"] for impact in impacts
                         if impact.get("severity", "").upper() in {"HIGH", "BLOCKER"}}
        elif issue.get("severity", "").upper() in {"CRITICAL", "BLOCKER"}:
            kind = legacy.get(issue.get("type"))
            if not kind:
                raise ValueError("Achado grave sem classificacao reconhecida")
            qualities = {kind}
        else:
            qualities = set()
        for quality in qualities:
            if quality not in counts:
                raise ValueError("Qualidade Sonar desconhecida")
            counts[quality] += 1
    return counts


def decide(issues, measures, approvals, baseline):
    """Somente achados graves novos bloqueiam ou exigem aprovacao extra."""
    counts = grave_counts(issues)
    lines = float(measures["new_lines_to_cover"])
    coverage = None if lines == 0 else float(measures["new_coverage"])
    if lines < 0 or (coverage is not None and not 0 <= coverage <= 100):
        raise ValueError("Métrica de cobertura inválida")
    required = baseline + (1 if counts["RELIABILITY"] else 0)
    reasons = []
    if counts["SECURITY"]:
        reasons.append("Há problemas de segurança no código novo.")
    if coverage is not None and coverage < 70:
        reasons.append("Cobertura do código novo inferior a 70%.")
    if approvals < required:
        reasons.append(f"Aprovações válidas: {approvals}/{required}.")
    return {"passed": not reasons, "counts": counts, "coverage": coverage,
            "approvals": approvals, "required": required, "reasons": reasons}


def count_approvals(reviews, sha, author, permissions):
    """Conta uma revisão vigente por pessoa, no SHA atual, com permissão de escrita."""
    latest = {}
    for review in sorted(reviews, key=lambda item: item["id"]):
        if review["state"] == "COMMENTED":
            continue
        latest[review["user"]["login"]] = review
    return sum(1 for login, review in latest.items()
               if login != author and review["user"].get("type") == "User"
               and review["state"] == "APPROVED" and review.get("commit_id") == sha
               and permissions.get(login) in {"write", "maintain", "admin"})


class API:
    def __init__(self, base, token):
        parsed = urlparse(base)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("URL da API deve usar HTTPS sem credenciais")
        self.base, self.token = base.rstrip("/"), token

    def call(self, path, method="GET", data=None):
        request = Request(self.base + path, method=method,
                          data=None if data is None else json.dumps(data).encode(),
                          headers={"Authorization": "Bearer " + self.token,
                                   "Accept": "application/json", "Content-Type": "application/json"})
        with urlopen(request, timeout=30) as response:
            return json.load(response)

    def pages(self, path):
        items = []
        for page in range(1, 101):
            batch = self.call(path + ("&" if "?" in path else "?") + f"per_page=100&page={page}")
            items.extend(batch)
            if len(batch) < 100:
                return items
        raise ValueError("Paginação excedeu limite seguro")


def scanner_context_matches(context, project, number, sha):
    properties = {}
    for line in context.splitlines():
        if "=" in line:
            key, value = line.strip().lstrip("- ").split("=", 1)
            properties[key.strip()] = value.strip()
    return (properties.get("sonar.projectKey") == project
            and properties.get("sonar.pullrequest.key") == str(number)
            and properties.get("sonar.scm.revision") == sha)


def metric_value(item):
    """Cloud usa periods[]; Server tambem pode devolver period/value."""
    period = item.get("period") or next(
        (entry for entry in item.get("periods", []) if entry.get("index") == 1), {})
    return period.get("value", item.get("value"))


def sonar_snapshot(sonar, project, number, sha):
    """Exige tarefa concluída ligada ao projeto, PR e SHA, não análise antiga."""
    activity = sonar.call("/api/ce/activity?" + urlencode({"component": project, "ps": 100}))
    matched = None
    for task in activity.get("tasks", []):
        details = sonar.call("/api/ce/task?" + urlencode({"id": task["id"], "additionalFields": "scannerContext"}))["task"]
        context = details.get("scannerContext", "")
        # A primeira análise desta PR é a mais recente. Não procura uma versão
        # antiga favorável se a mais recente pertence a outro commit.
        context_properties = dict(line.strip().lstrip("- ").split("=", 1)
                                  for line in context.splitlines() if "=" in line)
        if (context_properties.get("sonar.projectKey") == project
                and context_properties.get("sonar.pullrequest.key") == str(number)):
            if task.get("status") != "SUCCESS":
                raise ValueError("A análise mais recente desta PR não terminou com sucesso")
            if not scanner_context_matches(context, project, number, sha):
                raise ValueError("A análise mais recente da PR pertence a outro SHA")
            matched = details
            break
    if not matched:
        raise ValueError("Nenhuma análise concluída e verificável para o SHA atual; confira acesso ao scannerContext")
    query = {"component": project, "pullRequest": number,
             "metricKeys": "new_coverage,new_lines_to_cover"}
    raw = sonar.call("/api/measures/component?" + urlencode(query))["component"]["measures"]
    measures = {item["metric"]: metric_value(item) for item in raw}
    issues = []
    for page in range(1, 101):
        result = sonar.call("/api/issues/search?" + urlencode({"componentKeys": project,
                            "pullRequest": number, "resolved": "false", "ps": 100, "p": page}))
        issues.extend(result["issues"])
        if len(issues) >= result["paging"]["total"]:
            break
    else:
        raise ValueError("Quantidade de achados excedeu limite seguro")
    # Revalida que a análise da PR não foi substituída durante as consultas.
    after = sonar.call("/api/ce/activity?" + urlencode({"component": project, "ps": 100}))
    if [t["id"] for t in after.get("tasks", [])] != [t["id"] for t in activity.get("tasks", [])]:
        raise ValueError("Análises mudaram durante a consulta; reexecute a avaliação")
    return issues, measures


def evaluate_pr(github, sonar, repo, number, project):
    prefix = f"/repos/{repo}"
    pr = github.call(f"{prefix}/pulls/{number}")
    if pr["state"] != "open":
        return
    sha = pr["head"]["sha"]
    history = None
    state, description, result = "failure", "Validação Sonar pendente", None
    try:
        if not project or not sonar.token:
            raise ValueError("Configure SONAR_PROJECT_KEY e SONAR_POLICY_TOKEN")
        from urllib.error import HTTPError
        base = quote(pr["base"]["ref"], safe="")
        try:
            protection = github.call(f"{prefix}/branches/{base}/protection")
        except HTTPError as error:
            if error.code != 404:
                raise
            protection = {}
        baseline = (protection.get("required_pull_request_reviews") or {}).get("required_approving_review_count", 0)
        rules = github.call(f"{prefix}/rules/branches/{base}")
        for rule in rules:
            if rule["type"] == "pull_request":
                baseline = max(baseline, rule["parameters"]["required_approving_review_count"])
        reviews = github.pages(f"{prefix}/pulls/{number}/reviews")
        permissions = {}
        for login in {r["user"]["login"] for r in reviews if r["state"] == "APPROVED"}:
            permissions[login] = github.call(f"{prefix}/collaborators/{login}/permission")["permission"]
        approvals = count_approvals(reviews, sha, pr["user"]["login"], permissions)
        issues, measures = sonar_snapshot(sonar, project, number, sha)
        result = decide(issues, measures, approvals, baseline)
        try:
            old_issues = []
            for page in range(1, 101):
                old = sonar.call("/api/issues/search?" + urlencode({"componentKeys": project,
                                 "branch": pr["base"]["ref"], "resolved": "false", "ps": 100, "p": page}))
                old_issues.extend(old["issues"])
                if len(old_issues) >= old["paging"]["total"]:
                    break
            else:
                raise ValueError("Historico excedeu limite seguro")
            history = grave_counts(old_issues)
        except Exception:
            history = None  # Historico e apenas aviso, conforme regra aprovada.
        state = "success" if result["passed"] else "failure"
        description = "Política Sonar aprovada" if result["passed"] else "; ".join(result["reasons"])
    except Exception as error:
        # Não imprime respostas HTTP, headers ou tokens.
        description = "Validação indisponível: " + type(error).__name__
        if isinstance(error, (ValueError, KeyError)):
            description += " — " + str(error)
    if github.call(f"{prefix}/pulls/{number}")["head"]["sha"] != sha:
        return
    url = sonar.base + "/dashboard?" + urlencode({"id": project, "pullRequest": number})
    github.call(f"{prefix}/statuses/{sha}", "POST", {
        "state": state, "context": CHECK, "description": description[:140], "target_url": url})
    body = f"{MARKER}\n## Sonar {'aprovado ✅' if state == 'success' else 'pendente/reprovado ❌'}\n\nCommit: `{sha}`\n\n{description}\n"
    if result:
        coverage = "N/A: nenhuma linha nova instrumentável" if result["coverage"] is None else f'{result["coverage"]}% (mínimo 70%)'
        body += f'\n- Cobertura nova: {coverage}\n- Aprovações: {result["approvals"]}/{result["required"]}\n'
        body += f'- Segurança: {result["counts"]["SECURITY"]}\n- Confiabilidade: {result["counts"]["RELIABILITY"]}\n'
        body += f'- Manutenibilidade: {result["counts"]["MAINTAINABILITY"]} (somente aviso)\n'
    if history is None:
        body += "\nDivida grave da base: consulta indisponivel (somente aviso).\n"
    else:
        body += ("\nDivida grave existente na base (somente aviso): "
                 + ", ".join(f"{quality}={count}" for quality, count in history.items()) + "\n")
    body += "\nFiltro: Critical/Blocker (legado), High/Blocker (impactos). Achados menores nao bloqueiam.\n"
    body += f"\n[Ver análise]({url})\n\nO sucesso dos testes é exigido pelo check de testes separado (100%)."
    comments = github.pages(f"{prefix}/issues/{number}/comments")
    actor = github.call("/user")["login"]
    existing = next((c for c in comments if MARKER in (c.get("body") or "") and c["user"]["login"] == actor), None)
    path = f'{prefix}/issues/comments/{existing["id"]}' if existing else f"{prefix}/issues/{number}/comments"
    github.call(path, "PATCH" if existing else "POST", {"body": body})


def main():
    github = API("https://api.github.com", os.environ["GH_TOKEN"])
    sonar = API(os.environ.get("SONAR_HOST_URL", "https://sonarcloud.io"), os.environ["SONAR_TOKEN"])
    repo, project = os.environ["GITHUB_REPOSITORY"], os.environ["SONAR_PROJECT_KEY"]
    number = os.environ.get("PR_NUMBER", "")
    prs = [{"number": int(number)}] if number else github.pages(f"/repos/{repo}/pulls?state=open")
    for pr in prs:
        evaluate_pr(github, sonar, repo, pr["number"], project)


if __name__ == "__main__":
    main()
