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

---

See [endpoints.md](endpoints.md) for the full API reference.

---

## Testing

```bash
source venv/bin/activate
pytest tests -v
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

```bash
# List secrets
aws secretsmanager list-secrets --region eu-central-1

# Set Claude API key
aws secretsmanager put-secret-value \
  --secret-id claude-api-key \
  --secret-string "sk-your-real-api-key" \
  --region eu-central-1

# Verify
aws secretsmanager get-secret-value \
  --secret-id claude-api-key \
  --region eu-central-1
```
