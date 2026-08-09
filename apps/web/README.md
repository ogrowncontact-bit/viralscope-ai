# apps/web — ViralScope AI Frontend

Next.js 15 (App Router) + TypeScript + Tailwind v4 + shadcn/ui + TanStack Query + Clerk.

## Arquitetura

Estrutura _feature-based_: `app/` só contém rotas finas; regra de negócio de cada domínio (busca,
favoritos, estatísticas) vive em `src/features/<feature>/{api,components,types}`.

```
src/
├── app/                    # rotas (App Router)
│   ├── (dashboard)/        # protegido — auth.protect() no layout
│   │   └── dashboard/
│   ├── sign-in/, sign-up/  # páginas Clerk
│   └── status/             # health-check (Módulo 1)
├── components/
│   ├── ui/                 # primitivos shadcn — gerados, não editar à mão
│   ├── layout/              # sidebar, topbar, dashboard-shell, theme-toggle, user-menu
│   ├── states/              # EmptyState, ErrorState, ErrorBoundary, LoadingSpinner (reuso geral)
│   └── providers/           # ThemeProvider, QueryProvider
├── features/
│   ├── searches/           # busca + pesquisas recentes
│   ├── favorites/          # favoritos
│   ├── stats/               # cards de estatísticas do dashboard
│   └── billing/              # assinatura — planos, checkout e portal da Stripe (Módulo 6)
├── lib/                     # api-client (fetch + Bearer token do Clerk), env (zod), utils
└── middleware.ts            # clerkMiddleware() — contexto de auth para toda a app
```

Toda feature nova segue o mesmo gabarito de `searches`: `types/index.ts` (contrato espelhando o
DTO do backend), `api/get-*.ts` + `api/use-*.ts` (fetch + hook TanStack Query), `components/*`
(inclui um skeleton próprio). Erros de rota inteira usam `error.tsx`/`loading.tsx` (convenção
nativa do Next); falhas de um widget específico usam `<ErrorBoundary>` para não derrubar a página.

## Autenticação (Clerk)

- `ClerkProvider` envolve toda a aplicação em `app/layout.tsx` — por isso **nenhuma página
  renderiza sem `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`/`CLERK_SECRET_KEY` válidos**, mesmo páginas
  públicas como `/` ou `/status`.
- Proteção de rota usa o padrão atual da Clerk (_resource-based auth_): `await auth.protect()`
  dentro de `app/(dashboard)/layout.tsx`, não path-matching no middleware (API antiga
  `createRouteMatcher` está deprecated).
- Toda chamada autenticada à API usa `useAuth().getToken()` do Clerk, anexado como
  `Authorization: Bearer <token>` via `apiFetch` (`src/lib/api-client.ts`).

### Configurar suas próprias chaves

1. Crie um projeto em [dashboard.clerk.com](https://dashboard.clerk.com).
2. Copie `Publishable key` e `Secret key` para `apps/web/.env.local`:
   ```
   NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
   CLERK_SECRET_KEY=sk_test_...
   ```
3. Copie as mesmas chaves (mais o JWKS URL e issuer, disponíveis em
   _Configure → API Keys → Advanced_) para `apps/api/.env`:
   ```
   CLERK_JWKS_URL=https://<seu-domínio>.clerk.accounts.dev/.well-known/jwks.json
   CLERK_ISSUER=https://<seu-domínio>.clerk.accounts.dev
   ```
4. Configure um webhook em _Configure → Webhooks_ apontando para
   `<sua-api>/api/v1/webhooks/clerk`, eventos `user.created`, `user.updated`, `user.deleted`, e
   cole o _Signing Secret_ em `CLERK_WEBHOOK_SECRET` (`apps/api/.env`).

## Rodando localmente

```bash
pnpm install
pnpm dev
```

- `pnpm lint` — ESLint (inclui `@typescript-eslint/no-explicit-any` como erro)
- `pnpm typecheck` — typecheck (`tsc --noEmit`)
- `pnpm build` — build de produção

Esses três comandos, mais `pnpm format:check` (Prettier), rodam automaticamente em CI
(`.github/workflows/web.yml`) a cada push/PR para `main` — ver Módulo 7 no README raiz.
