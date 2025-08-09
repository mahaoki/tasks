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

### Variáveis de ambiente

As aplicações utilizam variáveis de ambiente para configurar chaves e serviços externos.
Crie um arquivo `.env` local baseado em `.env.example`:

```bash
cp .env.example .env
```

Este arquivo **não deve** ser versionado. Em pipelines de CI/CD, defina as mesmas
variáveis diretamente no ambiente de execução ou utilize mecanismos seguros como
Docker secrets e configurações da plataforma escolhida.

## Execução com Docker Compose

Para construir as imagens e iniciar todos os serviços, utilize:

```bash
docker compose build
docker compose up
```

As aplicações web e APIs estarão acessíveis em `app.tasks.localhost` e
`api.tasks.localhost`.

## Desenvolvimento local no macOS

Para executar a aplicação web localmente em um ambiente macOS:

1. Instale o [Node.js](https://nodejs.org/) 18 ou superior. Usuários de macOS podem utilizar o [Homebrew](https://brew.sh/):

   ```bash
   brew install node
   ```

2. Navegue até o diretório da aplicação e instale as dependências:

   ```bash
   cd web/app
   npm install
   ```

3. Copie o arquivo de variáveis de ambiente:

   ```bash
   cp .env.example .env.local
   ```

4. Inicie o servidor de desenvolvimento:

   ```bash
   npm run dev
   ```

5. Rode os testes (opcional):

   ```bash
   npm test        # testes unitários
   npm run test:e2e # testes end-to-end
   ```

O aplicativo estará disponível em [http://localhost:3000](http://localhost:3000).

## Debug

Algumas ferramentas úteis para depuração em ambiente local:

- **Mailhog**: servidor SMTP falso para inspecionar e-mails enviados.
  Após subir os containers com `docker compose up`, acesse a interface web em
  [http://localhost:8025](http://localhost:8025). Utilize o host `mailhog` e
  porta `1025` nas configurações de envio de e-mail das aplicações.
- **pgcli**: cliente interativo para o Postgres. Conecte-se ao banco de dados
  com `pgcli postgresql://app:app@localhost:5432/app` para executar consultas e
  inspeções de dados.

## Convenções de commit

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/) para padronizar as mensagens de commit.
Exemplos:

- `feat: adicionar rota de login`
- `fix: corrigir validação de token`

## Pull Requests

As Pull Requests devem seguir o template disponível em [`.github/pull_request_template.md`](.github/pull_request_template.md).
Documente as alterações, testes realizados e relacionamentos com issues.
