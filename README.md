# Language Learning App

## Environment Variables

Set these once to simplify all requests:

```bash
export API_URL="https://w88sqtf2y9.execute-api.eu-central-1.amazonaws.com"
export TOKEN="Bearer superSecretKetUntilISetUpJWT"
```

---

## Auth

All endpoints require:

```
Authorization: $TOKEN
```

---

## Create Conversation

POST /conversation

```bash
curl -X POST \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"personaId":"italian-tutor","title":"Test convo"}' \
  $API_URL/conversation
```

---

## List Conversations

GET /conversations

```bash
curl \
  -H "Authorization: $TOKEN" \
  $API_URL/conversations
```

---

## Get Conversation

GET /conversations/{conversationId}

```bash
export CONVERSATION_ID="8c8d0376-4097-4ec9-8c9a-b7611a305597"

curl \
  -H "Authorization: $TOKEN" \
  $API_URL/conversations/$CONVERSATION_ID
```

---

## Send Message

POST /conversations/{conversationId}/messages

```bash
export CONVERSATION_ID="8c8d0376-4097-4ec9-8c9a-b7611a305597"

curl -X POST \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"How do I say train station in Italian?"}' \
  $API_URL/conversations/$CONVERSATION_ID/messages
```



## Other commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
