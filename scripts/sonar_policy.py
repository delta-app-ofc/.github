"""Política Delta: segurança bloqueia, confiabilidade exige revisão adicional.

Executar somente por workflow confiável da branch base, sem executar código da PR.
As APIs são injetáveis para permitir testes sem tokens ou chamadas externas.
"""

import json
import os
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode, urlparse
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


def decide(issues, measures, no_files_analyzed=False):
    """Somente achados graves novos de segurança e cobertura abaixo de 70% bloqueiam a PR."""
    counts = grave_counts(issues)
    new_lines = metric_number(measures, "new_lines", whole=True)
    lines_to_cover = metric_number(measures, "new_lines_to_cover", whole=True)
    coverage_value = metric_number(measures, "new_coverage")

    if coverage_value is not None and coverage_value > 100:
        raise ValueError("Métrica Sonar inválida: new_coverage deve estar entre 0 e 100")

    if (no_files_analyzed and new_lines is None and lines_to_cover is None
            and coverage_value is None):
        coverage, coverage_na_reason = None, "nenhum arquivo analisado nesta PR"
    elif lines_to_cover == 0:
        coverage = None
        coverage_na_reason = "nenhuma linha nova instrumentável"
    elif new_lines == 0:
        if lines_to_cover is not None:
            raise ValueError("Métricas Sonar inconsistentes: new_lines é 0, mas há linhas a cobrir")
        coverage = None
        coverage_na_reason = "nenhuma linha nova no escopo analisado"
    elif lines_to_cover is None:
        raise ValueError("Métrica Sonar ausente: new_lines_to_cover para código novo")
    elif coverage_value is None:
        raise ValueError("Métrica Sonar ausente: new_coverage para linhas instrumentáveis")
    else:
        coverage = coverage_value
        coverage_na_reason = None

    reasons = []
    if counts["SECURITY"]:
        reasons.append("Há problemas de segurança no código novo.")
    if coverage is not None and coverage < 70:
        reasons.append("Cobertura do código novo inferior a 70%.")
    return {"passed": not reasons, "counts": counts, "coverage": coverage,
            "coverage_na_reason": coverage_na_reason,
            "reasons": reasons}


def metric_number(measures, name, whole=False):
    """Valida medida Sonar presente sem converter ausência ou valor inválido em zero."""
    if name not in measures:
        return None
    value = measures[name]
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"Métrica Sonar inválida: {name}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Métrica Sonar inválida: {name}") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"Métrica Sonar inválida: {name}")
    if whole:
        if number != number.to_integral_value():
            raise ValueError(f"Métrica Sonar inválida: {name}")
        return int(number)
    return float(number)


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


def pr_analysis_has_no_files(sonar, project, number):
    """Confirma uma árvore vazia da PR por rota independente das métricas."""
    query = {"component": project, "pullRequest": number, "qualifiers": "FIL", "ps": 1}
    result = sonar.call("/api/components/tree?" + urlencode(query))
    base = result.get("baseComponent")
    paging = result.get("paging")
    components = result.get("components")
    if (not isinstance(base, dict) or base.get("key") != project
            or str(base.get("pullRequest")) != str(number)):
        raise ValueError("Inventário Sonar não corresponde ao projeto e à PR atuais")
    if not isinstance(paging, dict) or not isinstance(components, list):
        raise ValueError("Resposta inválida do inventário de arquivos Sonar")
    total = metric_number({"total": paging.get("total")}, "total", whole=True)
    if total is None:
        raise ValueError("Inventário Sonar sem total de arquivos")
    if total == 0 and components == []:
        return True
    if total > 0 and len(components) == 1:
        return False
    raise ValueError("Inventário Sonar inconsistente")


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
             "metricKeys": "new_coverage,new_lines,new_lines_to_cover"}
    raw = sonar.call("/api/measures/component?" + urlencode(query))["component"]["measures"]
    measures = {item["metric"]: metric_value(item) for item in raw}
    no_files_analyzed = False
    if (not any(name in measures for name in
                ("new_lines", "new_lines_to_cover", "new_coverage"))):
        no_files_analyzed = pr_analysis_has_no_files(sonar, project, number)
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
    return issues, measures, no_files_analyzed


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
        issues, measures, no_files_analyzed = sonar_snapshot(sonar, project, number, sha)
        result = decide(issues, measures, no_files_analyzed=no_files_analyzed)
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
        coverage = (f'N/A: {result["coverage_na_reason"]}' if result["coverage"] is None
                    else f'{result["coverage"]}% (mínimo 70%)')
        body += f'\n- Cobertura nova: {coverage}\n'
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
