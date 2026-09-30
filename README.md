# Language Learning App

A serverless backend for an AI-powered language learning app. Users have conversations with an LLM tutor persona. The backend handles auth, conversation history, and per-user token budgets.

## Architecture

| Layer | Technology |
|---|---|
| Infrastructure | AWS CDK (TypeScript) |
| API | AWS API Gateway (HTTP API) |
| Compute | AWS Lambda (Python 3.12) |
| Database | AWS DynamoDB |
| Auth | Firebase Authentication |
| LLM | Anthropic Claude via [litellm](https://github.com/BerriAI/litellm) |
| Secrets | AWS Secrets Manager |
| Observability | AWS CloudWatch |

**How it works:** A user signs up via Firebase → a Firebase Cloud Function syncs the new user to the backend → an admin activates their account → the user can start conversations with a tutor persona and send messages backed by Claude.

Personas (system prompt, model, temperature, token limits) are stored in DynamoDB so they can be updated without redeployment.

## Requirements

- Node.js 20+ and npm (for AWS CDK)
- Python 3.12 and pip
- Docker (used by CDK to bundle Python Lambda dependencies)
- AWS CLI configured with credentials
- AWS account (deployed to `eu-central-1`)
- Firebase project with Authentication enabled
- Anthropic API key

## Future work

- Monthly token budget resets
- Fix token budget race condition (concurrent requests can both pass the budget check before either deducts)
- Rate limiting at API Gateway level
- Increase test coverage
- Look into CI/CD options

---

See [endpoints.md](endpoints.md) for the full API reference.

---

## Firebase Cloud Function setup

The Firebase Cloud Function syncs new users to the backend on signup. It reads two environment variables that must be set in the Firebase project:

- `AWS_LAMBDA_URL` — the full URL of the `/auth/newUser` endpoint
- `API_SECRET` — the internal secret stored in Secrets Manager (used to authenticate the call)

Set them with:

```bash
firebase functions:secrets:set AWS_LAMBDA_URL
firebase functions:secrets:set API_SECRET
```

After deploying the CDK stack, get the new API URL from the CDK output and update `AWS_LAMBDA_URL`. Then redeploy the Cloud Function:

```bash
cd firebaseCloudFunctions
firebase deploy --only functions
```

---

## Testing

```bash
source venv/bin/activate
pytest tests -v
```

This runs fully mocked — no network calls. `tests/test_llm_client_integration.py` makes a real call to Anthropic and is excluded by default (see `pytest.ini`); run it explicitly with a real `ANTHROPIC_API_KEY` set:

```bash
pytest tests -v -m integration
```

---

## CDK commands

* `npm run build` — compile TypeScript to JS
* `npx cdk synth` — synthesize CloudFormation templates
* `npx cdk diff` — compare deployed stack with current state
* `npx cdk deploy` — deploy to your default AWS account/region

---

## Activating a user

New users are created with `isActivated: false`. Set it to `true` to allow them to use the app:

```bash
aws dynamodb update-item \
  --table-name <UserMetaDataTable> \
  --key '{"pk": {"S": "USER#<uid>"}, "sk": {"S": "METADATA"}}' \
  --update-expression "SET isActivated = :t" \
  --expression-attribute-values '{":t": {"BOOL": true}}' \
  --region eu-central-1
```

Replace `<UserMetaDataTable>` with the actual table name from the CDK output and `<uid>` with the Firebase UID of the user.

---

## Secrets Manager commands

Three secrets must be populated after deploying the CDK stack.

```bash
# List secrets
aws secretsmanager list-secrets --region eu-central-1
```

**1. Claude API key**

```bash
aws secretsmanager put-secret-value \
  --secret-id claude-api-key \
  --secret-string "sk-ant-your-real-api-key" \
  --region eu-central-1
```

**2. Firebase service account**

Download the service account JSON from the Firebase console (Project Settings → Service Accounts → Generate new private key) and save it to `configs/firebase_admin.json` (gitignored). Then upload it:

```bash
aws secretsmanager put-secret-value \
  --secret-id firebase-service-account \
  --secret-string file://configs/firebase_admin.json \
  --region eu-central-1
```

**3. Internal secret (Cloud Function → backend)**

Choose any strong random string. This must match `API_SECRET` in the Firebase Cloud Function environment.

```bash
aws secretsmanager put-secret-value \
  --secret-id access-key-for-firebase-cloud-functions \
  --secret-string "your-strong-random-secret" \
  --region eu-central-1
```
