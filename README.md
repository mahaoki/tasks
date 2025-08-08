# Tasks Monorepo

Este repositório utiliza ferramentas de qualidade para garantir padrões consistentes de código.

## Configuração do ambiente

Instale as dependências de desenvolvimento e os hooks do pre-commit:

```bash
pip install pre-commit mypy pytest pytest-cov
pre-commit install
```

### Comandos locais

```bash
make lint       # formata e verifica estilos com pre-commit
make typecheck  # verifica tipos com mypy
make test       # executa pytest com cobertura
```

## Convenções de commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/) para padronizar as mensagens de commit.
Exemplos:

- `feat: adicionar rota de login`
- `fix: corrigir validação de token`

## Pull Requests

As Pull Requests devem seguir o template disponível em [`.github/pull_request_template.md`](.github/pull_request_template.md).
Documente as alterações, testes realizados e relacionamentos com issues.
