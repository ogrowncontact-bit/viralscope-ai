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
- `app/workers/` — worker de jobs assíncronos (fila Redis via `arq`), ver seção "Workers (Módulo 4)".

Esse padrão é o gabarito para toda feature nova: crie `models/<entidade>.py` (herdando os mixins),
`schemas/<feature>.py`, `repositories/interfaces/<feature>_repository.py` + implementação,
`services/<feature>_service.py`, `api/v1/routers/<feature>.py`, e registre os providers em
`core/dependencies.py`. Veja `health` (Módulo 1) e `searches`/`favorites`/`dashboard` (Módulo 2)
como referência.

## Domínio (Módulo 2)

7 tabelas, todas com PK UUID e timestamps: `users`, `searches`, `videos`, `analyses`, `favorites`,
`competitors`, `subscriptions`. `videos` já é populada pela ingestão (Módulo 3) e, a partir do
Módulo 4, também carrega os campos `transcript_*` (transcrição de áudio) e `metrics_synced_at`.
`analyses` é populada a partir do Módulo 5 (viral score, resumo, insights de IA) quando um usuário
dispara `POST /videos/{id}/analyze`. `subscriptions` é populada a partir do Módulo 6 (billing via
Stripe) — ver seção própria abaixo. Endpoints construídos cobrem só o que o dashboard consome
hoje: `me`, `searches`, `favorites`, `dashboard/stats`, `videos/{id}/transcribe`,
`videos/{id}/analyze`, `billing/*` — CRUD de `competitors` chega junto da feature que o usa.

### Autenticação

O backend não usa cookies de sessão — o frontend envia `Authorization: Bearer <token>` (JWT do
Clerk) em toda chamada autenticada. `core/security/clerk.py` verifica a assinatura via JWKS
(`PyJWKClient`, cacheado), issuer e `azp` (authorized party), sem depender de nenhum SDK Python da
Clerk. `core/dependencies.get_current_user` decodifica o token e faz *get-or-create* do usuário no
banco — o registro completo (nome/e-mail/avatar) é sincronizado de verdade via o webhook em
`api/v1/routers/webhooks/clerk.py`, assinado com Svix.

Variáveis necessárias (`apps/api/.env`): `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`.

## Workers (Módulo 4)

Fila de jobs assíncronos sobre Redis usando [`arq`](https://arq-docs.helpmanual.io/) (async-nativo,
combina com o resto do backend — SQLAlchemy asyncio, httpx, FastAPI). Definição em `app/workers/`:

- `app/workers/worker.py` — `WorkerSettings` (funções registradas, cron jobs, `on_startup`/
  `on_shutdown`). Roda com:
  ```bash
  poetry run arq app.workers.worker.WorkerSettings
  ```
  (também disponível como serviço `worker` no `docker-compose.yml`).
- `app/workers/context.py` — `video_repository_scope()`: jobs arq não têm `Depends` do FastAPI, então
  esse `@asynccontextmanager` abre uma `AsyncSession` (reusando a mesma `AsyncSessionFactory` de
  `app/db/session.py`) e devolve o repositório já construído.
- `app/workers/tasks/transcription.py` — `transcribe_video_job`: transcreve o áudio de um vídeo via
  `TranscriptionService` + `TranscriptionClientProtocol` (`app/integrations/interfaces/`). A
  implementação real, `WhisperTranscriptionClient`
  (`app/integrations/whisper_transcription_client.py`), baixa o áudio com `yt-dlp` e chama o endpoint
  REST `/v1/audio/transcriptions` (Whisper) da OpenAI via `httpx` — sem SDK, mesmo estilo de
  `youtube_client.py`. Precisa de `OPENAI_API_KEY`; sem ela, o job falha e marca
  `transcript_status = failed` com o erro em `transcript_error`.
  - **Disparo**: automático (fire-and-forget) a partir de `SearchService.create_search` para todo
    vídeo com `transcript_status = pending` recém-upsertado; ou manual via
    `POST /api/v1/videos/{id}/transcribe` (também serve para reprocessar um vídeo `failed`).
  - **Risco conhecido**: `yt-dlp` pode ser bloqueado por proteções anti-bot do YouTube a partir de
    IPs de datacenter/cloud em produção. Isso fica isolado atrás de `TranscriptionClientProtocol` —
    trocar a implementação não exige tocar em `TranscriptionService`, no job ou na tabela `videos`.
- `app/workers/tasks/metrics.py` — `sync_video_metrics_job`: cron (de hora em hora, ver
  `WorkerSettings.cron_jobs`) que reconsulta a YouTube Data API (`YouTubeClient.fetch_videos_by_id`,
  em lotes de até 50 ids) para atualizar `view_count`/`like_count`/`comment_count` dos vídeos
  favoritados por pelo menos um usuário — hoje o único conceito de "vídeo acompanhado" no domínio.

`ArqJobQueue` (`app/integrations/job_queue.py`) encapsula o pool de conexão com o Redis (lazy,
criado na primeira chamada) e usa um `_job_id` determinístico por vídeo (`transcribe-video-{id}`)
para aproveitar a dedupe nativa do arq e evitar enfileirar o mesmo vídeo duas vezes.

## Análise por IA (Módulo 5)

Também roda no worker do Módulo 4 (`app/workers/worker.py`), como um segundo job registrado em
`WorkerSettings.functions`:

- `app/workers/tasks/analysis.py` — `analyze_video_job`: analisa um vídeo via `AnalysisService` +
  `AnalysisClientProtocol` (`app/integrations/interfaces/analysis_client.py`). A implementação real,
  `ClaudeAnalysisClient` (`app/integrations/claude_analysis_client.py`), usa o **SDK oficial
  `anthropic`** (`AsyncAnthropic`) — diferente de `WhisperTranscriptionClient`/`YouTubeClient`
  (`httpx` puro), chamadas à própria API da Anthropic usam o SDK oficial. Modelo: `claude-haiku-4-5`
  (mais barato da família Claude — decisão deliberada de custo; não suporta `thinking` adaptativo
  nem `output_config.effort`, por isso nenhum dos dois é passado na chamada). Saída estruturada via
  `output_config.format` (`json_schema`), sem prefill de assistant.
  - **Disparo**: manual, por usuário, via `POST /api/v1/videos/{id}/analyze` — diferente da
    transcrição (automática), é uma ação explícita que sempre cria uma **nova linha** em `analyses`
    (sem cache/dedupe cross-user — N usuários analisando o mesmo vídeo geram N chamadas pagas à
    API). Bate com o contador "Análises geradas" do dashboard (`analyses_count` por usuário).
  - **Não bloqueia em transcrição**: se `video.transcript_status != completed` no momento em que o
    job roda, a análise segue só com os metadados do vídeo (título, descrição, canal, métricas,
    duração) — sem esperar nem re-enfileirar.
  - **Transcrição truncada**: `TRANSCRIPT_MAX_CHARS` (20.000 caracteres) em
    `claude_analysis_client.py` — vídeos muito longos enviam só o início da transcrição ao modelo.
  - Precisa de `ANTHROPIC_API_KEY`; sem ela, o job falha e marca `analyses.status = failed` com o
    erro em `analyses.error`.
- `ArqJobQueue.enqueue_analysis` usa `_job_id=f"analyze-{analysis_id}"` — dedupe por **análise**,
  não por vídeo (diferente de `enqueue_transcription`), já que cada disparo cria uma linha nova e
  todas devem rodar, mesmo para o mesmo vídeo.

## Billing (Módulo 6)

Liga a tabela `subscriptions` (existente desde o Módulo 2, até aqui vazia) a um fluxo de
pagamento real via **SDK oficial `stripe`** (mesma razão do `anthropic` no Módulo 5: chamada à
própria API do provedor de pagamento, não um serviço terceiro). Usa os métodos assíncronos
nativos do SDK (`create_async`/`retrieve_async`, disponíveis desde a v7 do `stripe-python`), que
usam `httpx` internamente (já é dependência do projeto) — dispensa `asyncio.to_thread` e mantém o
mesmo padrão de teste com `respx` usado para `anthropic`/Whisper.

- `app/integrations/interfaces/payment_client.py` + `app/integrations/stripe_payment_client.py` —
  `StripePaymentClient`: cria Checkout Session (assinatura, modo `subscription`), Billing Portal
  Session, busca o preço ao vivo de um Price ID (`get_price`) e busca uma assinatura completa
  (`get_subscription`, usado pelo webhook — ver abaixo). **Gotcha da API da Stripe** encontrado
  rodando contra o SDK de verdade: `current_period_end` não existe mais no nível raiz do objeto
  `Subscription` nas versões atuais da API — só em cada `items.data[].price` (uma assinatura pode
  ter múltiplos itens). `BillingService._resolve_plan_and_period_end` lê os dois do mesmo primeiro
  item, assumindo (como o resto do domínio) uma assinatura com um único item/preço.
- `app/repositories/subscription_repository.py` — `SqlAlchemySubscriptionRepository`:
  `upsert_by_user` (ON CONFLICT em `user_id`, mesmo padrão de `upsert_from_clerk` no
  `UserRepository`) usado no `checkout.session.completed`; `update_from_stripe`/`update_status`
  buscam por `stripe_customer_id` (índice `ix_subscriptions_stripe_customer_id`, migration
  `0004`) — os eventos de assinatura subsequentes da Stripe só trazem o `customer`, não o
  `user_id` interno.
- `app/services/billing_service.py` — `BillingService`:
  - `get_subscription`: sem linha em `subscriptions` (usuário nunca assinou) é tratado como Free,
    sem precisar popular a tabela na criação do usuário.
  - `list_plans`: **preço de Pro/Business nunca é hardcoded** — busca ao vivo na Stripe via
    `STRIPE_PRICE_ID_PRO`/`STRIPE_PRICE_ID_BUSINESS`, em paralelo (`asyncio.gather`); mudar o
    valor no Dashboard da Stripe não exige deploy. Falha ao buscar (chave ausente/inválida, price
    incorreto) degrada para `price_cents: null` em vez de derrubar a rota — mesmo espírito de
    resiliência do resto do domínio quando uma integração externa está fora do ar.
  - `create_checkout_session`/`create_portal_session`: redirecionamento para páginas hospedadas
    da Stripe (`session.url`) — **sem Stripe Elements**, então o frontend não precisa de
    `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`. Reaproveita `stripe_customer_id` já vinculado ao usuário
    (se existir) em vez de deixar a Stripe criar um Customer novo a cada checkout. Bloqueia um
    novo checkout (erro 400 tratado) se o usuário já tem uma assinatura paga em vigor (`active`/
    `trialing`/`past_due`) — troca de plano deve passar pelo Billing Portal, não por um segundo
    Checkout Session concorrente.
  - `handle_webhook_event`: dispatch em `checkout.session.completed` (busca a assinatura completa
    na Stripe via `get_subscription` e já grava plano/status/vigência corretos na hora — não
    depende da ordem de entrega dos webhooks da Stripe, que não é garantida),
    `customer.subscription.created`/`.updated` (resolve o plano a partir do Price ID do item da
    assinatura), `customer.subscription.deleted` (volta para Free/Canceled) e
    `invoice.payment_failed` (marca `past_due` sem tocar plano/vigência).
- `app/api/v1/routers/billing.py` — `GET /billing/subscription`, `GET /billing/plans` (público,
  sem dado de usuário), `POST /billing/checkout`, `POST /billing/portal`.
- `app/api/v1/routers/webhooks/stripe.py` — mesmo padrão do webhook do Clerk: lê `request.body()`
  bruto, verifica assinatura via `stripe.Webhook.construct_event` (não há abstração via
  `PaymentClientProtocol` para isso — verificação de webhook está amarrada aos bytes/headers
  crus da requisição, igual ao Clerk), 503 se `STRIPE_WEBHOOK_SECRET` não configurado, 401 em
  assinatura inválida.

Variáveis necessárias (`apps/api/.env`): `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`,
`STRIPE_PRICE_ID_PRO`, `STRIPE_PRICE_ID_BUSINESS`, `FRONTEND_URL` (usada para montar as URLs de
retorno pós-checkout/portal). Sem `STRIPE_SECRET_KEY`, `list_plans`/`checkout`/`portal` respondem
com preço indisponível / erro 400 tratado — nenhuma rota derruba a aplicação.

**Limitação conhecida**: a checagem de "já tem assinatura paga em vigor" em
`create_checkout_session` é check-then-act sem lock — dois cliques rápidos/duas abas antes da
primeira assinatura ser gravada no banco podem, em tese, resultar em duas Checkout Sessions
concorrentes. Aceito por ora dado o baixo custo/probabilidade num app early-stage; mitigação
futura seria um lock (ex.: `SELECT ... FOR UPDATE`) em torno da checagem, ou reconciliar via
webhook idempotente.

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

As migrations `0001_create_domain_tables`, `0002_add_video_transcript_fields`,
`0003_add_analysis_error_and_completed_at` e
`0004_add_subscription_stripe_customer_id_index` foram escritas à mão e já foram validadas
rodando de verdade contra um Postgres real (upgrade e downgrade). A partir delas, use
`--autogenerate` normalmente. Desde o Módulo 7, essa validação (upgrade → downgrade → upgrade
da cadeia inteira) roda automaticamente em CI a cada push/PR (`.github/workflows/api.yml`, job
`migrations`), contra um Postgres efêmero — não depende mais de rodar à mão a cada mudança.

## Testes

```bash
poetry run pytest
```

`tests/test_clerk_security.py` gera um par de chaves RSA no próprio teste para validar a
verificação de JWT sem depender de credenciais reais do Clerk. Os testes de routers
(`test_searches.py`, `test_favorites.py`, `test_dashboard.py`, `test_videos.py`) usam
`app.dependency_overrides` para trocar repositórios/integrações por mocks — não tocam banco nem
Redis de verdade. Os jobs do worker (`test_worker_jobs.py`) são chamados diretamente com um `ctx`
fake e `video_repository_scope`/`analysis_repository_scope` trocados via `monkeypatch` (jobs arq
não passam por `app.dependency_overrides`, que é específico do FastAPI).
`test_whisper_transcription_client.py` mocka `yt_dlp` e usa `respx` para a chamada à API Whisper,
sem baixar áudio nem chamar a OpenAI de verdade. `test_claude_analysis_client.py` usa `respx` para
mockar `POST /v1/messages` (o SDK `anthropic` usa `httpx` por baixo, então `respx` intercepta
normalmente) — sem chamar a Anthropic de verdade. `test_stripe_payment_client.py` mocka
`api.stripe.com` da mesma forma (o SDK `stripe` também roteia por `httpx` nos métodos `*_async`).
`test_stripe_webhook.py` monta uma assinatura HMAC válida manualmente (mesmo algoritmo do
`stripe.Webhook.construct_event`) para testar o roteiro de verificação ponta a ponta sem mockar
o SDK.
