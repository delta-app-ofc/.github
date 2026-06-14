import os
import re
import sys

def check_options(scope_list: list, pr_type_list: list, mandatory_checks_list: list, use_of_ai_list: list, str_pr_body: str) -> list[str]:
    body_lower = str_pr_body.lower()

    scope_ok = any(item.lower() in body_lower for item in scope_list)
    type_ok = any(item.lower() in body_lower for item in pr_type_list)
    mandatories_ok = all(item.lower() in body_lower for item in mandatory_checks_list)
    use_of_ai_ok = any(item.lower() in body_lower for item in use_of_ai_list)

    errors = []

    if not scope_ok:
        errors.append("❌ Nenhum módulo/escopo impactado foi selecionado no checklist.")

    if not type_ok:
        errors.append("❌ Nenhum tipo de PR (Conventional Commits) foi selecionado.")

    if not mandatories_ok:
        for check in mandatory_checks_list:
            if check.lower() not in body_lower:
                errors.append(f"❌ Item obrigatório não marcado: '{check.replace('- [x] ', '')}'.")

    if not use_of_ai_ok:
        errors.append("❌ Nenhum item de uso de IA foi selecionado.")

    return errors


def check_description(str_pr_body: str) -> list[str]:
    match = re.search(r"## 📄 Descrição(.*?)## ✨ Tipo de PR", str_pr_body, re.DOTALL)

    errors = []

    if not match:
        errors.append("❌ Erro: Não foi possível localizar a seção '## 📄 Descrição' ou '## ✨ Tipo de PR'.")
        return errors

    raw_description = match.group(1)
    clean_text = raw_description.replace(">", "").replace("\n", "").replace("*", "")

    template_phrases = [
        r"Descreva o que foi implementado\.",
        r"2° ANO: Lembre-se de registrar qual Requisito Funcional \(RF\) do documento de Engenharia de Software está sendo atendido\."
    ]

    for phrase in template_phrases:
        clean_text = re.sub(phrase, "", clean_text, flags=re.IGNORECASE)

    final_text = clean_text.strip()
    character_count = len(final_text)

    print(f"Texto útil detectado: '{final_text}'")
    print(f"Total de caracteres reais digitados pelo usuário: {character_count}")

    if character_count < 30:
        errors.append(
            f"❌ Erro: Descrição muito curta ou não preenchida (Apenas {character_count} caracteres úteis encontrados).")

    return errors

def main():
    pr_body = os.getenv("PR_BODY", "")
    pr_url = os.getenv("PR_URL", "")
    org_name = os.getenv("ORG_NAME", "")

    scope = [
        # primeiro ano
        "- [x] Backend (Java / Servlets / DAO)",
        "- [x] Frontend (HTML / CSS / Landing Page)",
        "- [x] Database (Modelo Lógico / Script SQL)",
        "- [x] Planilha de Controle / SO",

        # segundo ano
        "- [x] API REST (Spring Boot)",
        "- [x] Aplicação Dinâmica (React / TypeScript)",
        "- [x] Mobile (Android / iOS / Firebase)",
        "- [x] IA Multiagente (FastAPI / Langgraph)",
        "- [x] Banco de Dados (Postgres, MongoDB, Redis ou Neo4J)",
        "- [x] Infraestrutura / Pipeline de CI/CD ",
        "- [x] Gestão de projetos / Documentação / UX"
    ]

    pr_type = [
        "- [x] feat: Nova funcionalidade",
        "- [x] fix: Correção de bug",
        "- [x] refactor: Refatoração de código",
        "- [x] docs: Documentação (Swagger, Markdown, etc.)",
        "- [x] test: Implementação de testes (TDD)"
    ]

    mandatory_checks = [
        "- [x] Os commits deste branch seguem estritamente o padrão **Conventional Commits**.",
        "- [x] O código foi devidamente testado e não causa novos bugs."
    ]

    use_of_ai = [
        "- [x] Este código teve auxílio de IA.",
        "- [x] Este código foi feito 100% pelos integrantes."
    ]

    errors = check_options(scope, pr_type, mandatory_checks, use_of_ai, pr_body)
    errors += check_description(pr_body)

    if errors:
        print("\n🚨 [ATENÇÃO]: Erro de validação no preenchimento do Pull Request:\n")
        for error in errors:
            print(error)
        print("\n💡 Por favor, edite a descrição do seu PR e garanta:")
        print("   - Os checks necessários estão devidamente preenchidos")
        print("   - A PR tem descrição com 30 ou mais caracteres úteis\n")
        sys.exit(1)  # Bloqueia o PR legítimamente
    else:
        print("✅ Sucesso! O checklist do Pull Request foi preenchido corretamente.")
        sys.exit(0)  # Libera o pipeline

if __name__ == "__main__":
    print('teste de pr -> n considere')
    main()