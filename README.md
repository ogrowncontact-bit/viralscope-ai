# ViralScope AI

Plataforma SaaS que usa IA para identificar vídeos e canais do YouTube com alto potencial de
viralização — tendências emergentes, por que um vídeo viralizou, títulos e hooks vencedores, e
oportunidades de conteúdo para Shorts.

> Status: **Módulo 7 — CI (GitHub Actions).** Módulos 1–6 concluídos (estrutura inicial, auth,
> banco, dashboard, ingestão via YouTube Data API, transcrição via Whisper + coleta de métricas
> em segundo plano, análise por IA via Claude, billing via Stripe). Agora todo push/PR para
> `main` roda automaticamente lint, format-check, typecheck, testes (Pytest) e validação das
> migrations do Alembic contra um Postgres real — sem precisar de nenhum secret configurado. CD
> (deploy automático para Vercel/Railway) fica para um módulo futuro, quando essas contas
> existirem.

## Stack

| Camada       | Tecnologia                                                                                         |
| ------------ | -------------------------------------------------------------------------------------------------- |
| Frontend     | Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, TanStack Query, React Hook Form, Zod  |
| Backend      | FastAPI, Python, SQLAlchemy, Alembic                                                               |
| Banco        | Supabase PostgreSQL (real, já em uso — ver `apps/api/.env`)                                        |
| Cache / Fila | Redis + [`arq`](https://arq-docs.helpmanual.io/) (fila de jobs assíncronos, Módulo 4)              |
| Autenticação | Clerk                                                                                              |
| Pagamento    | Stripe (Checkout + Billing Portal hospedados, webhooks) — Módulo 6                                 |
| IA           | Whisper — OpenAI API (transcrição, Módulo 4) · Claude API — `claude-haiku-4-5` (análise, Módulo 5) |
| Deploy       | Vercel (web) · Railway (api) · Supabase (banco)                                                    |

## Arquitetura

Monorepo com pnpm workspaces. `apps/web` e `apps/api` são deployados de forma independente, mas
compartilham tooling, `.env` de referência e (futuramente) contratos de API gerados em `packages/`.

- **Frontend**: estrutura _feature-based_ — `src/app` só contém rotas finas; regra de negócio vive
  em `src/features/<feature>`. Auth via Clerk (`auth.protect()` nos layouts protegidos). Ver
  [`apps/web/README.md`](apps/web/README.md).
- **Backend**: Clean Architecture com Repository Pattern, Service Layer e Injeção de Dependência
  via `Depends` do FastAPI — `api → services → repositories → models`. JWT do Clerk verificado via
  JWKS, sem SDK Python oficial. Ver [`apps/api/README.md`](apps/api/README.md).

## Estrutura do repositório

```
viralscope-ai/
├── apps/
│   ├── web/     # Next.js 15
│   └── api/     # FastAPI
├── packages/    # reservado para código compartilhado (ex.: client OpenAPI)
├── infra/       # dockerfiles/manifests auxiliares
├── docker-compose.yml
└── .env.example
```

## Como rodar localmente

Pré-requisitos: Node.js ≥ 20, [pnpm](https://pnpm.io) (via `corepack enable`), Python ≥ 3.12,
[Poetry](https://python-poetry.org), uma conta [Supabase](https://supabase.com), uma conta
[Clerk](https://dashboard.clerk.com) (gratuitas) e uma chave da
[YouTube Data API](https://console.cloud.google.com/apis/library/youtube.googleapis.com) (para a
busca retornar vídeos — sem ela, a busca é salva mas retorna erro 502 ao consultar o YouTube).

```bash
# 1. Variáveis de ambiente
cp .env.example .env
# preencha apps/web/.env.local e apps/api/.env com suas chaves reais (Supabase, Clerk) —
# veja o passo a passo em apps/web/README.md

# 2a. Frontend
pnpm install
pnpm --filter web dev

# 2b. Backend (outro terminal)
cd apps/api
poetry install
poetry run alembic upgrade head   # cria as 7 tabelas no seu Postgres
poetry run uvicorn app.main:app --reload

# 2c. Worker (terceiro terminal) — transcrição (Whisper) + coleta de métricas + análise (Claude)
cd apps/api
poetry run arq app.workers.worker.WorkerSettings
```

- Frontend: http://localhost:3000 · dashboard em `/dashboard` (exige login)
- Backend: http://localhost:8000/docs (Swagger) · http://localhost:8000/api/v1/health
- Worker: precisa do Redis rodando (`docker-compose.yml` já sobe um). Sem `OPENAI_API_KEY`
  configurada, o job de transcrição roda mas falha (`transcript_status = failed`) — a busca em si
  não é afetada. Sem `ANTHROPIC_API_KEY`, o job de análise roda mas falha (`analyses.status =
failed`) — disparar `POST /videos/{id}/analyze` continua respondendo 202 normalmente.
- Billing: sem `STRIPE_SECRET_KEY`/`STRIPE_PRICE_ID_PRO`/`STRIPE_PRICE_ID_BUSINESS`, a tela
  `/dashboard/billing` continua abrindo (mostra "Preço indisponível" nos planos pagos) e assinar/
  gerenciar assinatura responde 400 tratado — nada quebra. Passo a passo de configuração da
  Stripe (produtos, preços recorrentes, webhook) em `.env.example`.

`docker-compose.yml` continua disponível para quem preferir Postgres/Redis locais em vez do
Supabase direto — nesse caso aponte `DATABASE_URL` para o container (`localhost:5432`) em vez da
connection string do Supabase.

## Qualidade de código

- **Lint/format**: ESLint + Prettier (TS/JS) e Ruff (Python), unificados num único hook de
  pre-commit via Husky + lint-staged — configurado na raiz (`package.json`).
- **CI** (Módulo 7, GitHub Actions): `.github/workflows/api.yml` roda `ruff check`, `ruff format
--check`, `pytest`, e um job separado `migrations` que valida a cadeia completa de migrations
  do Alembic — upgrade → downgrade → upgrade — contra um Postgres real efêmero.
  `.github/workflows/web.yml` roda `prettier --check`, `eslint`, `tsc --noEmit`, `next build`.
  Ambos disparam em todo push/PR para `main`, filtrados por path (só rodam quando o app
  correspondente muda), sem exigir nenhum secret configurado.
- **Testes**: Pytest (`apps/api/tests`, 130 testes — Clerk JWT com par RSA gerado no teste, routers
  com repositórios mockados, clientes YouTube/Whisper/Claude/Stripe mockados via `respx`, jobs do
  worker chamados diretamente com repositório fake, webhook da Stripe validado com assinatura HMAC
  real). Vitest no frontend chega num módulo futuro — o frontend é validado via
  `eslint`/`tsc --noEmit`/`next build` (também em CI).
- **Tipagem**: `strict` no TypeScript, proibido `any` (regra de ESLint `@typescript-eslint/no-explicit-any`).

```bash
pnpm install && pnpm prepare   # instala husky (uma vez, após clonar)
```

## Roadmap de módulos

Cada módulo abaixo é implementado e aprovado separadamente:

1. ✅ Estrutura inicial
2. ✅ Dashboard, Auth (Clerk) e domínio de dados
3. ✅ Ingestão de dados — YouTube Data API, popula `videos`
4. ✅ Workers assíncronos (Redis via `arq`) — transcrição Whisper, coleta periódica de métricas
5. ✅ Camada de IA (Claude) — `analyses`: viral score, resumo, títulos vencedores, hooks,
   oportunidades de conteúdo. Disparo manual via `POST /videos/{id}/analyze`
6. ✅ Billing (Stripe) — liga a tabela `subscriptions` a um fluxo de pagamento real
7. ✅ CI (GitHub Actions) — lint, format-check, typecheck, testes (Pytest) e validação de
   migrations do Alembic contra Postgres real, em todo push/PR para `main` (este módulo). CD
   (deploy automático) fica para um módulo futuro.

## Licença

Proprietário — todos os direitos reservados.
