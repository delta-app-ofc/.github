# CI técnica

Em pull requests e por execução manual, o workflow `test.yml` verifica a sintaxe dos arquivos Python e executa os testes unitários existentes com Python 3.12, sem credenciais ou chamadas reais ao GitHub.

## Execução local

```bash
python -m compileall -q scripts tests
python -m unittest discover -s tests -v
```

Os testes cobrem o bypass emergencial com respostas simuladas. A compilação verifica sintaxe, mas não comprova o comportamento dos demais scripts nem a integração com a API do GitHub. A governança de PR continua no workflow `local_checks.yml`.
