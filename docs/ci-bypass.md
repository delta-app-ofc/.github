# Bypass emergencial do CI Delta

## Objetivo

A label `ci-bypass` permite pular temporariamente as validações de governança
do Delta. Não é evidência de que o código passou nos testes e não libera checks
de outros workflows ou aplicações.

## Ativação e revogação

1. Publique primeiro o script e os workflows deste repositório na `main`.
2. Publique nos satélites o caller com os eventos `labeled` e `unlabeled`.
3. Crie a label `ci-bypass` em cada repositório, em Issues → Labels → New label.
4. Registre na PR a justificativa da emergência.
5. Aplique a label usando a conta `samuelpimentah`.
6. Confira o resumo da execução: ele deve registrar o bypass, não testes aprovados.
7. Remova a label para reativar as validações.

O bypass permanece ativo enquanto a label aplicada pela conta autorizada estiver
presente, inclusive em novas execuções e novos commits. Uma reaplicação por outra
conta não autoriza o bypass. Não deixe a label em PRs que não sejam emergenciais.

## Como a autorização funciona

O script consulta as labels atuais e todas as páginas do histórico de eventos
da PR pela API do GitHub. A última aplicação de `ci-bypass` precisa ter sido feita
por `samuelpimentah`, sem intermediação de GitHub App. A identidade de quem apenas
reexecuta o Actions não é usada como autorização.

Aplicação por outra pessoa mantém as validações normais. Falha de consulta da API
faz o job falhar, sem liberar o bypass. O token precisa conseguir ler a PR, suas
labels e seu histórico.

Com o bypass autorizado, não executamos os validadores de commits, `.gitignore`,
checklist nem o roteamento de revisores. Nenhum checkbox da PR é marcado
automaticamente por esse caminho.

## Limite da proteção

O GitHub não restringe uma label específica a uma pessoa: a restrição está na
autorização feita pelo script. Proteja alterações deste script e dos workflows
com revisão obrigatória. Pessoas que podem alterar livremente as automações
podem também alterar a política de autorização.

## Testes locais

```bash
python -m unittest discover -s tests -v
```

Os testes simulam as respostas da API; não substituem uma execução real do Actions.
