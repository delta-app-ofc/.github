"""Valida o .gitignore mínimo e a proteção de arquivos .env do Projeto Delta."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CHECKBOX_TEXT = (
    "As variáveis de ambiente (.env) foram configuradas e **não** foram versionadas."
)
ALLOWED_ENV_FILES = {".env.example", ".env.sample", ".env.template", ".env.test"}


def active_rules(content: str) -> list[str]:
    """Retorna somente as regras ativas de um conteúdo de .gitignore."""
    return [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def contains_rules_in_order(
    project_rules: list[str], required_rules: list[str]
) -> bool:
    """Confirma que todas as regras obrigatórias existem na ordem definida."""
    required_index = 0

    for rule in project_rules:
        has_next_rule = required_index < len(required_rules)
        if has_next_rule and rule == required_rules[required_index]:
            required_index += 1

    return required_index == len(required_rules)


def tracked_env_files(repository: Path) -> list[str]:
    """Lista arquivos .env protegidos que já estejam rastreados pelo Git."""
    result = subprocess.run(
        ["git", "-C", str(repository), "ls-files"],
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("❌ Não foi possível consultar os arquivos rastreados pelo Git.")
        print(result.stderr.strip())
        sys.exit(1)

    tracked = []
    for relative_path in result.stdout.splitlines():
        filename = Path(relative_path).name
        is_environment_file = filename == ".env" or filename.startswith(".env.")
        if is_environment_file and filename not in ALLOWED_ENV_FILES:
            tracked.append(relative_path)

    return tracked


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
        print("✅ O checkbox de proteção do .env já estava marcado.")
        return

    if unchecked not in body:
        print(
            "❌ O checkbox de proteção do .env não foi encontrado na descrição da PR."
        )
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
        print("❌ A validação passou, mas não foi possível marcar o checkbox na PR.")
        print(edit_result.stderr.strip())
        sys.exit(1)

    print("✅ Checkbox de proteção do .env marcado automaticamente na PR.")


def main() -> None:
    """Executa as validações do .gitignore e atualiza a Pull Request."""
    parser = argparse.ArgumentParser(
        description="Valida o .gitignore do projeto contra o padrão mínimo do Delta."
    )
    parser.add_argument("--project", default=".gitignore", help=".gitignore do projeto")
    parser.add_argument("--reference", required=True, help=".gitignore padrão do Delta")
    parser.add_argument("--repository", default=".", help="Diretório do repositório")
    parser.add_argument("--pr-url", default=os.getenv("PR_URL", ""), help="URL da PR")
    args = parser.parse_args()

    project_path = Path(args.project)
    reference_path = Path(args.reference)

    if not reference_path.is_file():
        print(f"❌ Arquivo-base não encontrado: {reference_path}")
        sys.exit(1)

    reference_content = reference_path.read_text(encoding="utf-8-sig")

    if not project_path.is_file():
        project_rules = []
    else:
        project_rules = active_rules(project_path.read_text(encoding="utf-8-sig"))

    required_rules = active_rules(reference_content)
    rules_are_valid = contains_rules_in_order(project_rules, required_rules)
    tracked_env = tracked_env_files(Path(args.repository))

    if not rules_are_valid or tracked_env:
        print("❌ O projeto não atende ao padrão mínimo de proteção do .gitignore.")

        if tracked_env:
            print("\nArquivos de ambiente rastreados indevidamente:")
            for relative_path in tracked_env:
                print(f"  - {relative_path}")

        print(
            "\nO .gitignore deve conter, no mínimo, exatamente estas regras "
            "e nesta ordem:"
        )
        print("\n--- INÍCIO DO .gitignore OBRIGATÓRIO ---")
        print(reference_content.rstrip())
        print("--- FIM DO .gitignore OBRIGATÓRIO ---")
        print(
            "\nRegras adicionais podem ser incluídas, sem alterar a ordem "
            "das obrigatórias."
        )
        sys.exit(1)

    print("✅ O .gitignore contém todas as regras mínimas do Projeto Delta.")
    print("✅ Nenhum arquivo .env protegido está sendo rastreado pelo Git.")
    mark_checkbox(args.pr_url)


if __name__ == "__main__":
    main()
