# AGENTS.md

Guidance for AI coding agents working in this repo. See `README.md` for
human-facing setup/deploy instructions; this file covers conventions an
agent needs to not get wrong on the first try.

## Commands

- `npm run build` — compile CDK TypeScript to JS
- `npx cdk synth` — synthesize CloudFormation templates
- `npx cdk diff` — compare deployed stacks with current state
- `npx cdk deploy` — deploy to the default AWS account/region (requires
  Docker running — CDK bundles Python lambda dependencies)
- `source venv/bin/activate && pytest tests -v` — run lambda unit tests
  (fully mocked, no network calls; `pytest.ini` excludes the
  `integration` marker by default). `tests/test_llm_client_integration.py`
  makes a real call to Anthropic and only runs with an explicit
  `pytest tests -v -m integration` plus a real `ANTHROPIC_API_KEY`.
- CDK stack tests live in `test/` (`npm test` / `jest`), separate from the
  Python lambda tests in `tests/`

## Repo map

- `bin/langapp.ts` — app entrypoint; instantiates all CDK stacks and wires
  their dependencies with explicit `.addDependency()` calls. Stack order
  matters (Secret → Data → Auth → Api → Observability).
- `lib/*.ts` — one CDK stack per file (`data-stack.ts`, `auth-stack.ts`,
  `api-stack.ts`, `secretsStack.ts`, `observability-stack.ts`).
- `lambda_functions/<name>/app.py` — one Python lambda per route/action
  (`listConversations`, `getConversation`, `createConversation`,
  `sendMessage`, `newUserSetup`, `authorizer`). Each lambda's dependencies
  (e.g. `sendMessage/llm_client.py`) are colocated in the same directory
  because CDK bundles each lambda folder independently.
- `lambda_functions/shared/` — currently an empty stub. `response()`,
  `now_iso()`, and `get_body()` are copy-pasted identically across
  `listConversations`, `createConversation`, `getConversation`,
  `sendMessage`, and `newUserSetup`'s `app.py` files instead of living
  here. **Until that's consolidated, any fix to one of those helpers
  must be applied to all five files, not just one.**
- `tests/` — pytest unit tests per lambda. `authorizer/app.py` currently
  has no test file — don't assume coverage exists just because the
  sibling lambdas have it.
- `firebaseCloudFunctions/` — Firebase Cloud Function that syncs new
  signups to the `/auth/newUser` lambda.
- `devFrontend/` — Vite/React dev harness for manually exercising the
  API. Not production UI.

## Data model conventions

Source of truth for item shapes and key construction is the lambda code
itself, not `lib/data-stack.ts` (which only declares generic `pk`/`sk`
string keys). Read before adding any new query or item shape:

- `lambda_functions/createConversation/app.py` — constructs all three
  item shapes (persona lookup, conversation item, starter message item)
- `lambda_functions/sendMessage/app.py` — constructs message items and
  the user-metadata key, and shows the query pattern for the last N
  messages in a conversation

Follow the existing `pk`/`sk` shape exactly (e.g. `USER#{userId}` /
`CONVERSATION#{conversationId}`, `CONVERSATION#{conversationId}` /
`MESSAGE#{timestamp}#{messageId}`) — don't invent a new key format for a
new access pattern without checking whether an existing one already
covers it.

## Personas live in DynamoDB, not code

Persona config (system prompt, model, temperature, token limits) is
stored in `PromptTable` (`PROMPT#{personaId}` / `VERSION#1`), read via
`get_persona_from_ddb()` in `createConversation/app.py` and
`sendMessage/app.py`. Never hardcode a persona's prompt/model/params in
lambda code — add or edit the DynamoDB item instead.

## Token budget accounting

`sendMessage/app.py` enforces the budget atomically via a reserve-then-
reconcile pattern (`reserve_token_budget()` / `reconcile_token_usage()`):
it atomically reserves `maxTokens` against `tokenBudgetTotal` with a
`ConditionExpression` before calling the LLM (rejecting with 429 on
`ConditionalCheckFailedException`), then does an unconditional follow-up
`ADD` to true up `tokensUsed` once the actual token count is known. This
exists because DynamoDB condition expressions can't do arithmetic across
two attributes (`tokenBudgetTotal - tokensUsed >= :x` isn't valid) — don't
"simplify" this back into a single non-atomic read-then-compare, that's
exactly the race it fixes.

## Auth context

`userId` comes from `event.requestContext.authorizer.lambda.userId`,
populated by the Lambda authorizer (`lambda_functions/authorizer/app.py`)
after verifying a Firebase ID token. Auth is Firebase-only — the old
hardcoded test-token bypass has been removed. Don't reintroduce a bypass
or assume one still exists.

## Secrets

Three secrets in AWS Secrets Manager, injected into lambdas via env vars
(never inline a key in code):

1. Claude/Anthropic API key
2. Firebase service account JSON
3. Internal shared secret used by the Firebase Cloud Function to call
   `/auth/newUser`

`configs/firebase_admin.json` (the local copy of the service account
used to seed the secret) must stay gitignored — never commit it.

## Known tech debt

Don't "fix" these incidentally while touching unrelated code, and don't
assume they're already handled:

- No API Gateway throttling — only a CloudWatch alarm on high invocation
  rate, which is alerting, not rate limiting.
- No CI/CD (no GitHub Actions workflows in this repo).
- No monthly token-budget reset mechanism.
- CORS on the HTTP API is hardcoded to `http://localhost:5173`
  (`lib/api-stack.ts`).
