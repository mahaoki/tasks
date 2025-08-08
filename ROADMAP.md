# ROADMAP — Sistema de Gestão de Tarefas (MVP: Auth + Users + Frontend inicial)

> **Escopo do MVP**: 2 microserviços **FastAPI** (Auth e Users) desacoplados, **Next.js** (frontend) com telas **Login**, **Esqueceu a Senha** e **Dashboard** inicial. **Docker Compose** com **Traefik** como API Gateway, domínios locais **api.tasks.localhost** e **app.tasks.localhost**. **Banco único** (Postgres) com **schemas separados por serviço**, **Alembic** e **migrations individuais**. `seeds` individuais (primeiro usuário admin).

---

## 0. Padrões de Arquitetura & Qualidade (aplicados desde o dia 1)

- **Linguagem & Tooling**
  - Backend: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x, Alembic, httpx, passlib[bcrypt].
  - Frontend: Next.js (TypeScript), ShadCN UI, TailwindCSS, React Query.
  - Infra Dev: Docker/Compose, Traefik, Postgres, Redis (session/rate limit), Mailhog (SMTP fake).
- **Separação de responsabilidades**
  - `auth-service`: autenticação, tokens (JWT), refresh, políticas de escopo.
  - `user-service`: CRUD de usuários e perfis (roles), relação usuário↔setores (placeholder para futuro), perfis e permissões básicas.
- **Banco de dados**
  - Um Postgres **compartilhado**, schemas **`auth`** e **`users`**.
  - Conexões independentes por serviço (pool separado, role de DB separada por serviço).
- **Segurança**
  - **JWT** com chave assimétrica (RS256/Ed25519) e **rotation** planejada.
  - **Rate limiting** no gateway (IP) e por credencial (Redis). CORS estrito.
  - Política de senhas (mínimo 12 chars, ban de senhas comuns), hashing **bcrypt** com custo revisado.
  - Secrets via `.env` (dev) e variáveis de ambiente (CI/CD). Nunca comitar secrets.
- **Observabilidade**
  - OpenAPI exposto por serviço; logs estruturados (JSON), métricas Prometheus via `/metrics` (v1), tracing OpenTelemetry (v1).
- **Qualidade**
  - Linters/formatters (ruff + black + isort), mypy (strict-ish), pytest + coverage.
  - Conventional Commits, PR template, CODEOWNERS, pre-commit hooks.

---

## 1. Estrutura de repositório (monorepo)

```
repo/
  docker/                # compose files, traefik, init SQL, etc.
    traefik/
      traefik.yml
      dynamic.yml
    postgres/
      init/00-create-schemas.sql
  services/
    auth-service/
      app/
        api/routers/
        core/ (config, security, deps)
        domain/ (models, schemas)
        services/ (usecases)
        db/ (session, migrations)
      tests/
      pyproject.toml
      requirements.txt
      Dockerfile
      entrypoint.sh
    user-service/
      app/...
      tests/
      pyproject.toml
      requirements.txt
      Dockerfile
      entrypoint.sh
  web/
    app/
      src/
        pages/
        components/
        lib/
      package.json
      next.config.js
      Dockerfile
  .env.example
  compose.yml
  Makefile
  README.md
  ROADMAP.md
```

---

## 2. Planejamento por Fases

### Fase A — Fundação
- [ ] Criar monorepo e estrutura inicial (pastas acima).
- [ ] Definir **convenções** (format, lint, typecheck, test) e **pre-commit**.
- [ ] Adicionar **compose.yml** com serviços: traefik, postgres, redis, mailhog, auth-service, user-service, web.
- [ ] Provisionar Traefik com middlewares (gzip, headers, rate-limit), routers `api.tasks.localhost` (backends) e `app.tasks.localhost` (frontend).
- [ ] Postgres com **schemas** `auth` e `users` no init SQL.
- [ ] Documentar `.env.example` (chaves JWT, DATABASE_URLs, SMTP, CORS).

### Fase B — Auth Service
- [ ] FastAPI skeleton + healthcheck `/healthz`.
- [ ] SQLAlchemy models (schema `auth`): `auth_users`, `refresh_tokens`, `password_resets`, `audit_log`.
- [ ] Alembic init + primeira migration.
- [ ] Endpoints:
  - [ ] `POST /auth/register` (apenas admin no MVP via seed).
  - [ ] `POST /auth/login` (email + senha) → `access_token` (15min) + `refresh_token` (7d).
  - [ ] `POST /auth/refresh`.
  - [ ] `POST /auth/forgot-password` → e-mail com token (Mailhog em dev).
  - [ ] `POST /auth/reset-password` (token de 30 min, one-time use).
  - [ ] `GET /auth/me` (claims + roles obtidas do user-service).
- [ ] Segurança & políticas:
  - [ ] Hash de senha com bcrypt e pepper opcional.
  - [ ] JWT RS256/EdDSA com `kid` no header e jwks em `/.well-known/jwks.json`.
  - [ ] Throttling de login (p.ex. 5/min por IP + user) via Redis.
  - [ ] CORS: `https://app.tasks.localhost` apenas.
  - [ ] CSRF não se aplica a JSON-only; cookies `HttpOnly` apenas se optarmos por cookie mode.
- [ ] Auditoria de eventos (login_success, login_failed, password_reset_requested, password_changed).

### Fase C — User Service
- [ ] FastAPI skeleton + `/healthz`.
- [ ] Models (schema `users`): `users` (id, email, name, active), `roles` (Gerente, Coordenador, Líder Técnico, Colaborador), `user_roles` (n:N), `sectors` (seed inicial), `user_sectors`.
- [ ] Alembic init + migrations.
- [ ] Endpoints (protegidos via JWT + escopos):
  - [ ] `GET /users/me` (perfil completo).
  - [ ] `GET /users` (paginado, filtros por role/sector, somente admin/gerente).
  - [ ] `POST /users` (admin/gerente cria colaborador/coordenador/líder técnico).
  - [ ] `PATCH /users/{id}` (ativar/desativar, nome, setores, roles).
  - [ ] `GET /roles` e `GET /sectors`.
- [ ] Integração com Auth: validação de `sub`, checagem de escopos/roles por claim/idp.
- [ ] Auditoria: user_created, role_assigned, sector_assigned, profile_updated.

### Fase D — Seeds & Dados de Partida
- [ ] Scripts de **seed** independentes por serviço (via CLI FastAPI ou script Python):
  - [ ] `auth-service`: criar admin técnico (email, senha forte), política de token, jwks inicial.
  - [ ] `user-service`: criar setores (`video`, `copy`, `design`, `ux`, `social`) e vincular admin ao papel **Gerente**.
- [ ] Makefile targets: `make db.up`, `make migrate`, `make seed`, `make restart`.

### Fase E — Frontend
- [ ] Bootstrap Next.js (TS) + Tailwind + ShadCN.
- [ ] Configurar base URL `https://api.tasks.localhost` (env), React Query, interceptors.
- [ ] Páginas:
  - [ ] **Login**: formulário com validação + feedback de erros do Auth.
  - [ ] **Esqueceu a senha**: request token e tela de redefinição.
  - [ ] **Dashboard** (placeholder): saudação, perfil do usuário (chamar `/users/me`), cards de atalhos.
- [ ] Componentes UI: Input, Button, Form, Alert, Toast, Skeleton, ProtectedRoute.
- [ ] Gestão de sessão (access + refresh), auto-refresh (silent), logout seguro.
- [ ] Tratamento de estados (loading, error), empty states, A11y e dark mode.

### Fase F — Infra, Segurança e Observabilidade
- [ ] Traefik middlewares: `redirect-to-https` (simulado), `secure-headers` (HSTS dev off), `rate-limit`, `compress`.
- [ ] Certificados dev (mkcert) opcionais; em prod usar ACME.
- [ ] Logs JSON e correlação por `X-Request-ID` (middleware em serviços e gateway).
- [ ] Health & readiness endpoints expostos; `/metrics` (Prometheus) previsto.
- [ ] Backups locais de Postgres (cron) e política de retenção (dev simples).

---

## 3. Compose & Traefik (resumo conceitual)

- **Traefik**: routers `api@docker` → regra `Host(`api.tasks.localhost`)`, `web` middleware; serviço aponta para backends (auth/user) via prefixos: `/auth`, `/users` (ou subrouters dedicados). Frontend via `Host(`app.tasks.localhost`)`.
- **CORS**: liberado **somente** para `https://app.tasks.localhost` (ou `http` em dev), `Authorization` e `Content-Type` headers.
- **Rede**: `tasks_net` bridge dedicada. Postgres e Redis sem portas expostas publicamente; acesso só pela rede interna.

> **Dica**: usar path prefix no gateway (ex.: `/auth`, `/users`) simplifica DNS; em produção, opte por subdomínios separados (`auth.api…`, `users.api…`) se desejar.

---

## 4. Banco de Dados & Migrações

- **Init SQL** cria schemas `auth` e `users`.
- Cada serviço define **`search_path`** para seu schema.
- Alembic por serviço (versionamento independente). Policy de migração: `offline` (gerar) + `online` (aplicar), bloqueio por tag em CI.
- Scripts de verificação: `migrate:check` (dry-run), `migrate:apply` (dev), `migrate:rollback` (se aplicável).

---

## 5. Segurança (MVP)

- Autenticação JWT **curta** (15 min) + refresh (7 dias). Blacklist de refresh tokens revogados.
- Rotação de chaves (kid) — manter 2–3 chaves ativas no JWKS; script de rotação.
- Rate limit de login (p.ex. 5 req/min/IP + usuário).
- Política de senha (12+ chars, checagem de senhas piores conhecidas).
- Sanitização de erros: respostas genéricas em login/reset.
- CORS, headers de segurança (Traefik), gzip/deflate habilitado.
- Dados sensíveis nunca em logs. PII mascarada.

---

## 6. Testes (MVP)

- **Backend**: pytest (unit + integration com DB/Redis via fixtures). Cobrir:
  - Auth: login/refresh/reset, lockout, jwks.
  - Users: RBAC básico (Gerente vs Colaborador), CRUD e filtros.
- **Frontend**: unit (Vitest) para componentes, E2E (Playwright) para fluxo Login → Dashboard.
- **Contract tests**: validar schemas OpenAPI e status codes.

---

## 7. CI/CD (Dev/Staging futuramente)

- Pipeline: linters + typecheck + testes + build docker + `alembic upgrade head` em ambiente de teste.
- Cache de dependências (pip/poetry e npm). SBOM (syft) opcional.
- Trunk-based com feature flags simples (env vars).

---

## 8. Tarefas Detalhadas (Checklist de Implementação)

### Repo e Infra
- [ ] Criar monorepo e arquivos básicos: `README.md`, `ROADMAP.md`, `LICENSE`.
- [ ] Adicionar `.editorconfig`, `.gitignore`, `.gitattributes`.
- [ ] Configurar **pre-commit** com black, ruff, isort, trailing-whitespace, end-of-file-fixer.
- [ ] Criar `Makefile` com alvos: `up`, `down`, `build`, `logs`, `format`, `lint`, `test`, `migrate`, `seed`.
- [ ] `docker/traefik/traefik.yml` (providers.docker, entrypoints), `dynamic.yml` (middlewares/headers/rate-limit).
- [ ] `docker/postgres/init/00-create-schemas.sql` (create schema auth; create schema users; grants).
- [ ] `compose.yml` com serviços, redes e volumes. Postgres e Redis sem portas externas.

### Auth Service
- [ ] `requirements.txt`/`pyproject.toml` (fastapi, uvicorn, sqlalchemy, alembic, pydantic, passlib, pyjwt, httpx, python-jose opcional, redis, structlog).
- [ ] `Dockerfile` com user não-root, `entrypoint.sh` aplicando migrations antes do start.
- [ ] Config `Settings` (pydantic): DB URL, JWT keys, SMTP, CORS, RATE_LIMIT.
- [ ] Models & migrations: `auth_users`, `refresh_tokens`, `password_resets`, `audit_log`.
- [ ] Routers: `/auth/login`, `/auth/refresh`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/me`.
- [ ] Segurança: JWT service (sign/verify), jwks endpoint, throttling.
- [ ] Seed: criar usuário admin (email/senha do `.env`) e chave JWKS inicial.
- [ ] Testes unitários e integração (DB em container).

### User Service
- [ ] `requirements.txt`/`pyproject.toml` similar (sem libs desnecessárias do auth).
- [ ] `Dockerfile` + `entrypoint.sh` (migrate → start).
- [ ] Config `Settings`: DB URL (schema users), AUTH_PUBLIC_JWKS URL.
- [ ] Models & migrations: `users`, `roles`, `user_roles`, `sectors`, `user_sectors`.
- [ ] Routers: `GET /users/me`, `GET /users`, `POST /users`, `PATCH /users/{id}`, `GET /roles`, `GET /sectors`.
- [ ] RBAC e integração com JWT (scope/roles). Validações de input (pydantic) e paginação.
- [ ] Seeds: setores default e vínculo de admin como **Gerente**.
- [ ] Testes unitários e integração.

### Frontend (Next.js)
- [ ] Setup TS, Tailwind, ShadCN; layout base, ThemeToggle, Toaster.
- [ ] Config `.env.local` com `NEXT_PUBLIC_API_BASE=https://api.tasks.localhost`.
- [ ] Serviço de API (fetch/http client) com interceptadores (refresh token).
- [ ] Páginas:
  - [ ] `/login` (form + validação + erros do servidor).
  - [ ] `/forgot-password` (pedir email → feedback). `/reset-password` (token flow).
  - [ ] `/dashboard` (protegida; SSR/CSR com checagem de sessão; mostrar `users/me`).
- [ ] Componentes ShadCN: `Button`, `Input`, `Form`, `Card`, `Alert`, `Badge`, `Spinner`.
- [ ] Testes básicos (unit + e2e login).

### Gateway & Segurança
- [ ] Traefik routers:
  - [ ] `api.tasks.localhost` → middlewares `secure-headers`, `rate-limit`, `compress`.
  - [ ] PathPrefix(`/auth`) → `auth-service` ; PathPrefix(`/users`) → `user-service`.
  - [ ] `app.tasks.localhost` → frontend.
- [ ] CORS: permitir somente `app.tasks.localhost` em ambos serviços.
- [ ] Rate limit por IP (p.ex. 100 req/min) + regra específica para `/auth/login` (5/min).
- [ ] Headers de segurança (XSS, no sniff, frame deny exceto necessário).

### Operação & Observabilidade
- [ ] Healthchecks e timeouts configurados (readiness/liveness nos serviços).
- [ ] Logs com `request_id`; propagar `X-Request-ID` do Traefik.
- [ ] Documentar como debugar (links do Mailhog, pgcli, etc.).

---

## 9. Critérios de Aceitação do MVP
- Login, refresh e reset de senha funcionando ponta-a-ponta (incluindo e-mail em dev via Mailhog).
- Dashboard exibe dados de `/users/me` com roles e setores do usuário logado.
- Seeds criam: admin (Auth) e setores + role Gerente (Users).
- Domínios locais acessíveis: `https://app.tasks.localhost` e `https://api.tasks.localhost`.
- Migrations aplicadas automaticamente no start sem race.
- CORS e rate limit ativos. Nenhum secret em git. Testes principais passando no CI.

---

## 10. Riscos & Mitigações
- **Acoplamento indesejado** via banco único → Mitigar com schemas e roles de DB separadas, e evitar cross-schema direto; sempre via APIs.
- **Rotação de chaves JWT** → Planejar cron de rotação + retenção; invalidar refresh antigos.
- **Ambiente dev HTTPS** → mkcert opcional; em prod usar ACME/TLS automático.
- **Gerenciamento de versão de migrações** → disciplina de PRs e bloqueios em CI.

---

## 11. Próximos Passos (após MVP)
- Métricas (Prometheus), tracing (OTel), dashboards (Grafana).
- Harden TLS, WAF/IDS opcional, secret manager.
- Integração de UI de gerenciamento de usuários/roles no app.
- Início do **Task Service** e **Campaign Service**.

---

## 12. Anexos (snippets conceituais)

### 12.1. Exemplo de label Traefik (serviço Auth)
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.auth.rule=Host(`api.tasks.localhost`) && PathPrefix(`/auth`)"
  - "traefik.http.routers.auth.entrypoints=web"
  - "traefik.http.middlewares.secure-headers.headers.stsSeconds=31536000"
  - "traefik.http.middlewares.rate-limit.ratelimit.average=100"
```

### 12.2. Entrypoint de serviço (migrate → run)
```bash
#!/usr/bin/env bash
set -euo pipefail
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 12.3. Init SQL de schemas
```sql
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS users;
```

---

> **Pronto para implementar**: com este roadmap, basta gerar os skeletons, preencher Dockerfiles e compose, criar migrations e seeds, e começar os fluxos de autenticação e usuários. Em seguida, a UI do frontend poderá consumir `/auth` e `/users` para entregar Login/Reset/Dashboard.
