# ViralScope AI

Plataforma SaaS que usa IA para identificar vídeos e canais do YouTube com alto potencial de
viralização — tendências emergentes, por que um vídeo viralizou, títulos e hooks vencedores, e
oportunidades de conteúdo para Shorts.

> Status: **Módulo 2 — Dashboard, Auth (Clerk) e domínio de dados.** Estrutura inicial (Módulo 1)
> concluída; agora há autenticação, banco com 7 tabelas migradas no Supabase, e um dashboard
> funcional (busca, pesquisas recentes, favoritos, estatísticas). A _descoberta de vídeos por IA_
> em si (ingestão do YouTube, análise) ainda não existe — chega nos Módulos 3–5.

## Stack

| Camada       | Tecnologia                                                                                        |
| ------------ | ------------------------------------------------------------------------------------------------- |
| Frontend     | Next.js 15 (App Router), TypeScript, TailwindCSS, shadcn/ui, TanStack Query, React Hook Form, Zod |
| Backend      | FastAPI, Python, SQLAlchemy, Alembic                                                              |
| Banco        | Supabase PostgreSQL (real, já em uso — ver `apps/api/.env`)                                       |
| Cache / Fila | Redis _(Módulo 4)_                                                                                |
| Autenticação | Clerk                                                                                             |
| Pagamento    | Stripe _(Módulo 6)_                                                                               |
| IA           | Claude API, OpenAI API, Whisper _(Módulo 5)_                                                      |
| Deploy       | Vercel (web) · Railway (api) · Supabase (banco)                                                   |

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
[Poetry](https://python-poetry.org), uma conta [Supabase](https://supabase.com) e uma conta
[Clerk](https://dashboard.clerk.com) (gratuitas).

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
```

- Frontend: http://localhost:3000 · dashboard em `/dashboard` (exige login)
- Backend: http://localhost:8000/docs (Swagger) · http://localhost:8000/api/v1/health

`docker-compose.yml` continua disponível para quem preferir Postgres/Redis locais em vez do
Supabase direto — nesse caso aponte `DATABASE_URL` para o container (`localhost:5432`) em vez da
connection string do Supabase.

## Qualidade de código

- **Lint/format**: ESLint + Prettier (TS/JS) e Ruff (Python), unificados num único hook de
  pre-commit via Husky + lint-staged — configurado na raiz (`package.json`).
- **Testes**: Pytest (`apps/api/tests`, 15 testes — Clerk JWT com par RSA gerado no teste, routers
  com repositórios mockados). Vitest no frontend chega num módulo futuro.
- **Tipagem**: `strict` no TypeScript, proibido `any` (regra de ESLint `@typescript-eslint/no-explicit-any`).

```bash
pnpm install && pnpm prepare   # instala husky (uma vez, após clonar)
```

## Roadmap de módulos

Cada módulo abaixo é implementado e aprovado separadamente:

1. ✅ Estrutura inicial
2. ✅ Dashboard, Auth (Clerk) e domínio de dados (este módulo)
3. Ingestão de dados — YouTube Data API, popula `videos`
4. Workers assíncronos (Redis) — transcrição Whisper, coleta de métricas
5. Camada de IA (Claude / OpenAI) — `analyses`: viral score, insights, títulos, hooks
6. Billing (Stripe) — liga a tabela `subscriptions` a um fluxo de pagamento real
7. CI/CD (GitHub Actions)

## Licença

Proprietário — todos os direitos reservados.
