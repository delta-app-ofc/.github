"""Valida as mensagens dos commits incluídos em uma Pull Request do Delta."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


ALLOWED_TYPES = ("feat", "fix", "refactor", "docs", "test", "style")
CHECKBOX_TEXT = (
    "Os commits deste branch seguem estritamente o padrão **Conventional Commits**."
)
COMMIT_PATTERN = re.compile(
    rf"^({'|'.join(ALLOWED_TYPES)})(\([a-z0-9][a-z0-9._/-]*\))?!?: \S.+$"
)


def get_commits(repository: Path, base: str, head: str) -> list[tuple[str, str]]:
    """Retorna hash e título dos commits presentes no intervalo."""
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "log",
            "--format=%H%x09%s",
            f"{base}..{head}",
        ],
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("❌ Não foi possível obter os commits da Pull Request.")
        print(result.stderr.strip())
        sys.exit(1)

    commits = []
    for line in result.stdout.splitlines():
        commit_hash, subject = line.split("\t", maxsplit=1)
        commits.append((commit_hash, subject))

    return commits


def is_valid_subject(subject: str) -> bool:
    """Valida Conventional Commits e títulos especiais gerados pelo Git."""
    is_initial_commit = subject.casefold() == "initial commit"
    is_merge_commit = subject.startswith("Merge ")
    return bool(COMMIT_PATTERN.fullmatch(subject)) or is_initial_commit or is_merge_commit


def publish_pr_body(body: str) -> None:
    """Disponibiliza o corpo atualizado para os próximos passos do mesmo job."""
    github_env = os.getenv("GITHUB_ENV", "")
    if not github_env:
        return

    delimiter = "DELTA_PR_BODY_END"
    with Path(github_env).open("a", encoding="utf-8") as env_file:
        env_file.write(f"PR_BODY<<{delimiter}\n{body}\n{delimiter}\n")


def mark_checkbox(pr_url: str) -> None:
    """Marca na descrição da PR o checkbox validado automaticamente."""
    if not pr_url:
        print(
            "ℹ️ PR_URL não informado; o checkbox não será atualizado "
            "nesta execução local."
        )
        return

    view_result = subprocess.run(
        ["gh", "pr", "view", pr_url, "--json", "body", "--jq", ".body"],
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
    )

    if view_result.returncode != 0:
        print("❌ Não foi possível ler a descrição atual da Pull Request.")
        print(view_result.stderr.strip())
        sys.exit(1)

    body = view_result.stdout.rstrip("\r\n")
    unchecked = f"- [ ] {CHECKBOX_TEXT}"
    checked = f"- [x] {CHECKBOX_TEXT}"

    if checked.lower() in body.lower():
        print("✅ O checkbox de Conventional Commits já estava marcado.")
        publish_pr_body(body)
        return

    if unchecked not in body:
        print("❌ O checkbox de Conventional Commits não foi encontrado na PR.")
        print(f"Item esperado: {unchecked}")
        sys.exit(1)

    updated_body = body.replace(unchecked, checked, 1)
    edit_result = subprocess.run(
        ["gh", "pr", "edit", pr_url, "--body", updated_body],
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        env=os.environ.copy(),
    )

    if edit_result.returncode != 0:
        print("❌ Os commits são válidos, mas não foi possível marcar o checkbox.")
        print(edit_result.stderr.strip())
        sys.exit(1)

    publish_pr_body(updated_body)
    print("✅ Checkbox de Conventional Commits marcado automaticamente na PR.")


def main() -> None:
    """Executa a validação dos commits informados pela linha de comando."""
    parser = argparse.ArgumentParser(
        description=(
            "Valida os commits da Pull Request conforme o padrão do Projeto Delta."
        )
    )
    parser.add_argument("--base", required=True, help="SHA base da Pull Request")
    parser.add_argument("--head", required=True, help="SHA final da Pull Request")
    parser.add_argument("--repository", default=".", help="Diretório do repositório")
    parser.add_argument("--pr-url", default=os.getenv("PR_URL", ""), help="URL da PR")
    args = parser.parse_args()

    commits = get_commits(Path(args.repository), args.base, args.head)
    invalid_commits = [
        (commit_hash, subject)
        for commit_hash, subject in commits
        if not is_valid_subject(subject)
    ]

    if invalid_commits:
        print("❌ Foram encontrados commits fora do padrão do Projeto Delta:\n")
        for commit_hash, subject in invalid_commits:
            print(f"  - {commit_hash[:7]} {subject}")

        print("\nFormato obrigatório:")
        print("  <tipo>(escopo opcional): descrição")
        print(f"\nTipos permitidos: {', '.join(ALLOWED_TYPES)}")
        print("\nExemplos válidos:")
        print("  feat: adiciona consulta de consumo")
        print("  fix(api): corrige validação do usuário")
        print("  docs: atualiza instruções do projeto")
        print("  Merge branch 'main' into feat/minha-alteracao")
        print("  Initial Commit")
        sys.exit(1)

    print(f"✅ {len(commits)} commit(s) seguem o padrão do Projeto Delta.")
    mark_checkbox(args.pr_url)


if __name__ == "__main__":
    main()
