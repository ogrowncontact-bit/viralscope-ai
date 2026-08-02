# apps/api — ViralScope AI Backend

FastAPI em Clean Architecture: `api → services → repositories → models`.

## Camadas

- `app/api/v1/routers/` — HTTP puro. Recebe request, chama um `service` via `Depends`, devolve um
  `schema` (DTO). Nunca contém regra de negócio nem acessa o banco diretamente.
- `app/services/` — casos de uso. Orquestra repositórios, aplica regras. Não conhece FastAPI nem
  SQLAlchemy — só depende das interfaces em `repositories/interfaces`.
- `app/repositories/interfaces/` — contratos (`typing.Protocol`) que os services dependem.
- `app/repositories/` — implementações concretas dos contratos (hoje: SQLAlchemy/Postgres).
- `app/models/` — entidades SQLAlchemy (ORM), mapeiam tabelas. `mixins.py` centraliza PK UUID e
  `created_at`/`updated_at` — toda tabela nova herda `UUIDPrimaryKeyMixin, TimestampMixin`.
- `app/schemas/` — DTOs Pydantic de entrada/saída da API. Nunca reexportam `models` diretamente.
- `app/core/` — configuração (`config.py`), injeção de dependência (`dependencies.py`), logging,
  e `core/security/clerk.py` (verificação de JWT via JWKS).
- `app/db/` — engine/sessão async e `Base` declarativa.
- `app/workers/` — reservado para jobs assíncronos (fila Redis) a partir do Módulo 4.

Esse padrão é o gabarito para toda feature nova: crie `models/<entidade>.py` (herdando os mixins),
`schemas/<feature>.py`, `repositories/interfaces/<feature>_repository.py` + implementação,
`services/<feature>_service.py`, `api/v1/routers/<feature>.py`, e registre os providers em
`core/dependencies.py`. Veja `health` (Módulo 1) e `searches`/`favorites`/`dashboard` (Módulo 2)
como referência.

## Domínio (Módulo 2)

7 tabelas, todas com PK UUID e timestamps: `users`, `searches`, `videos`, `analyses`, `favorites`,
`competitors`, `subscriptions`. `videos`/`analyses` são catálogo/IA — ficam vazias até os Módulos
4/5 (ingestão do YouTube e análise por IA) existirem. Endpoints construídos cobrem só o que o
dashboard consome hoje: `me`, `searches`, `favorites`, `dashboard/stats` — CRUD de
`videos`/`analyses`/`competitors`/`subscriptions` chega junto das features que os usam.

### Autenticação

O backend não usa cookies de sessão — o frontend envia `Authorization: Bearer <token>` (JWT do
Clerk) em toda chamada autenticada. `core/security/clerk.py` verifica a assinatura via JWKS
(`PyJWKClient`, cacheado), issuer e `azp` (authorized party), sem depender de nenhum SDK Python da
Clerk. `core/dependencies.get_current_user` decodifica o token e faz *get-or-create* do usuário no
banco — o registro completo (nome/e-mail/avatar) é sincronizado de verdade via o webhook em
`api/v1/routers/webhooks/clerk.py`, assinado com Svix.

Variáveis necessárias (`apps/api/.env`): `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`.

## Rodando localmente

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

Docs interativas: http://localhost:8000/docs

## Migrations

```bash
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "descrição"   # para novas mudanças de schema
```

A migration `0001_create_domain_tables` foi escrita à mão (não havia conexão de banco disponível
no momento da criação para autogenerate) e já foi validada rodando de verdade contra um Postgres
real. A partir dela, use `--autogenerate` normalmente.

## Testes

```bash
poetry run pytest
```

`tests/test_clerk_security.py` gera um par de chaves RSA no próprio teste para validar a
verificação de JWT sem depender de credenciais reais do Clerk. Os testes de routers
(`test_searches.py`, `test_favorites.py`, `test_dashboard.py`) usam `app.dependency_overrides`
para trocar repositórios por mocks — não tocam banco de verdade.
