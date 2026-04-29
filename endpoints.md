```bash
export API_URL="https://w88sqtf2y9.execute-api.eu-central-1.amazonaws.com"
export TOKEN="Bearer <firebase-id-token>"
```

---

## Auth

All endpoints require:

```
Authorization: $TOKEN
```

---

## Create Conversation

POST /conversations

```bash
curl -X POST \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"personaId":"italian-tutor","title":"Test convo"}' \
  $API_URL/conversation
```

```
{"conversationId": "6cea48d7-aca5-4c8e-9a2e-5bc32cdb3c73", "personaId": "italian-tutor", "title": "Test convo", "createdAt": "2026-03-30T18:34:52Z", "assistantMessage": {"messageId": "a4f7d12f-1a80-4eef-a460-02fc5501abea", "role": "assistant", "content": "Ciao! Io sono il tuo tutor di italiano. Come ti chiami?", "createdAt": "2026-03-30T18:34:52Z"}}%  
```
---

## List Conversations

GET /conversations

```bash
curl \
  -H "Authorization: $TOKEN" \
  $API_URL/conversations
```

```
{"items": [{"conversationId": "6cea48d7-aca5-4c8e-9a2e-5bc32cdb3c73", "personaId": "italian-tutor", "title": "Test convo", "createdAt": "2026-03-30T18:34:52Z", "updatedAt": "2026-03-30T18:34:52Z", "lastMessageAt": "2026-03-30T18:34:52Z", "lastMessagePreview": "Ciao! Io sono il tuo tutor di italiano. Come ti chiami?"}, {"conversationId": "8c8d0376-4097-4ec9-8c9a-b7611a305597", "personaId": "italian-tutor", "title": "Test convo", "createdAt": "2026-03-15T14:17:16Z", "updatedAt": "2026-03-30T18:08:32Z", "lastMessageAt": "2026-03-30T18:08:32Z", "lastMessagePreview": "Ciao! Sto bene, grazie per aver chiesto. E tu, come stai oggi?\n\n\u00c8 sempre bello iniziare una conversazione con un saluto cordiale. In italiano si usa spesso \"Ciao\" come saluto informale, oppure \"Buongiorno\" o \"Buonasera\" a seconda dell'orario.\n\nDimmi, hai qualche altra domanda sull'italiano che posso aiutarti a praticare? Sono qui per guidarti passo passo nell'apprendimento della lingua."}, {"conversationId": "94a23f84-f81c-4914-a301-53919d264dba", "personaId": "italian-tutor", "title": "test-convo-5", "createdAt": "2026-03-28T20:52:56Z", "updatedAt": "2026-03-28T22:37:52Z", "lastMessageAt": "2026-03-28T22:37:52Z", "lastMessagePreview": "Ottimo, parliamo di come programmare in Python! Ecco alcune idee per iniziare:\n\nIl modo pi\u00f9 semplice \u00e8 utilizzare il modulo \"math\" integrato in Python. Puoi importarlo all'inizio del tuo codice e usare le funzioni matematiche di base, come:\n\nimport math\npeso = 70\naltezza = 1.75\nbmi = peso / (altezza ** 2)\nprint(f\"Il tuo BMI \u00e8: {bmi:.2f}\")\n\nQuesto calcola l'indice di massa corporea (BMI) in modo semplice.\n\nUn'altra opzione \u00e8 utilizzare librerie specializzate come \"numpy\" o \"scipy\" che offrono molte funzioni matematiche avanzate.\n\nInoltre, potresti creare delle tue funzioni personalizzate per calcolare il peso ideale, il fabbisogno calorico, ecc.\n\nQuale di queste opzioni ti sembra pi\u00f9 interessante per iniziare? Fammi sapere se hai altre domande!"}, {"conversationId": "6d4b1cbf-c694-42ea-bb90-9d94323b6df9", "personaId": "italian-tutor", "title": "Test convo", "createdAt": "2026-03-28T20:52:34Z", "updatedAt": "2026-03-28T20:52:34Z", "lastMessageAt": "2026-03-28T20:52:34Z", "lastMessagePreview": "Ciao! Io sono il tuo tutor di italiano. Come ti chiami?"}, {"conversationId": "e7d93afc-6e84-41d5-91f6-3c74da7a3325", "personaId": "italian-tutor", "title": "test-convo-3", "createdAt": "2026-03-28T16:24:40Z", "updatedAt": "2026-03-28T16:26:42Z", "lastMessageAt": "2026-03-28T16:26:42Z", "lastMessagePreview": "Ah, capisco! Volevi dire \"perch\u00e9 vorresti acquistare una casa\", in italiano. \u00c8 una buona idea voler comprare una casa! \u00c8 un grande passo, ma pu\u00f2 essere molto soddisfacente. Hai gi\u00e0 iniziato a cercare case in Italia?"}, {"conversationId": "86551da9-47ea-4ba3-aecc-fb89f571ae2c", "personaId": "italian-tutor", "title": "test-convo-2", "createdAt": "2026-03-28T15:59:30Z", "updatedAt": "2026-03-28T15:59:38Z", "lastMessageAt": "2026-03-28T15:59:38Z", "lastMessagePreview": "Ciao! Come posso aiutarti oggi?"}]}%
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

```
": "assistant", "content": "Ciao! Mi chiamo [Assistente]. Come stai oggi? Come posso aiutarti con il tuo italiano?", "createdAt": "2026-03-28T15:04:06Z"}, {"messageId": "73176d17-fa9e-42eb-9f49-cf288f06dd3b", "role": "user", "content": "Ciao! Mi chiamo", "createdAt": "2026-03-28T15:04:06Z"}, {"messageId": "321a0ce7-03d7-4fca-9a61-0f841681506f", "role": "user", "content": "Sto Bene oggi!", "createdAt": "2026-03-28T15:04:50Z"}, {"messageId": "45d29b6a-78b0-4c78-8743-0a82cbf1c72c", "role": "assistant", "content": "Molto bene! Sono felice di sentirti dire che stai bene oggi. Dimmi, qual \u00e8 la tua lingua madre? Hai gi\u00e0 studiato l'italiano prima?", "createdAt": "2026-03-28T15:04:50Z"}, {"messageId": "74d3d530-2a5a-4286-9a62-dd64cbad0810", "role": "assistant", "content": "Ah, capisco. Scusa, ho presumo che tu parlassi italiano. Possiamo continuare in inglese se preferisci. \n\nDimmi, qual \u00e8 la tua lingua madre? Hai gi\u00e0 studiato l'italiano in precedenza o \u00e8 la prima volta che lo studi?", "createdAt": "2026-03-28T15:56:12Z"}, {"messageId": "e79f588a-f91e-40ba-bfde-2bd4dacf3378", "role": "user", "content": "i dont understand", "createdAt": "2026-03-28T15:56:12Z"}, {"messageId": "55c40d50-2897-456b-82b7-c3357bb25f1d", "role": "user", "content": "How do I say train station in Italian?", "createdAt": "2026-03-30T15:56:46Z"}, {"messageId": "f9f2f524-34c6-4bd4-8cb0-8b349e43a66e", "role": "assistant", "content": "Nessun problema! Vediamo come si dice \"stazione dei treni\" in italiano:\n\nLa stazione dei treni\n\nMolto bene! Puoi usare questa frase per chiedere indicazioni o per dire dove devi andare, per esempio:\n\n\"Dov'\u00e8 la stazione dei treni?\"\n\"Devo andare alla stazione dei treni.\"\n\nHai qualche altra domanda sull'italiano? Sono qui per aiutarti a imparare!", "createdAt": "2026-03-30T15:56:46Z"}, {"messageId": "4d04efe4-dcf2-4fdc-8a4e-1acdcea1905e", "role": "user", "content": "Ciao come stai", "createdAt": "2026-03-30T18:08:32Z"}, {"messageId": "78ca3827-c424-44bd-8846-3f82386292f4", "role": "assistant", "content": "Ciao! Sto bene, grazie per aver chiesto. E tu, come stai oggi?\n\n\u00c8 sempre bello iniziare una conversazione con un saluto cordiale. In italiano si usa spesso \"Ciao\" come saluto informale, oppure \"Buongiorno\" o \"Buonasera\" a seconda dell'orario.\n\nDimmi, hai qualche altra domanda sull'italiano che posso aiutarti a praticare? Sono qui per guidarti passo passo nell'apprendimento della lingua.", "createdAt": "2026-03-30T18:08:32Z"}]}%    
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

```
{"conversationId": "8c8d0376-4097-4ec9-8c9a-b7611a305597", "userMessage": {"messageId": "8c4e6e25-3564-4da8-96f5-dbe58cd44ef4", "role": "user", "content": "How do I say train station in Italian?", "createdAt": "2026-03-30T18:36:02Z"}, "assistantMessage": {"messageId": "5fc4ae32-ba0b-4bf6-97dd-6a62838c3fcd", "role": "assistant", "content": "Ah, s\u00ec, la stazione dei treni! Te l'ho gi\u00e0 detto prima, ma \u00e8 importante praticare.\n\nIn italiano, per dire \"stazione dei treni\" si dice:\n\nLa stazione dei treni\n\nPuoi usare questa frase in vari contesti, ad esempio:\n\n- Dov'\u00e8 la stazione dei treni? \n- Devo andare alla stazione dei treni.\n- Prendo il treno alla stazione dei treni.\n\nHai capito bene? Fammi sapere se hai bisogno di qualche altro esempio per memorizzare questa espressione.", "createdAt": "2026-03-30T18:36:02Z"}, "usage": {"prompt_tokens": 732, "completion_tokens": 149, "total_tokens": 881}}
```

---

## User Sync

POST /auth/newUser

Called automatically by the Firebase Cloud Function on signup. The `x-internal-secret` header must match the secret stored in Secrets Manager.

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-internal-secret: <firebase-sync-secret>" \
  -d '{
    "userId": "<firebase-uid>",
    "name": "John",
    "email": "john@example.com",
    "authProvider": "google"
  }' $API_URL/auth/newUser
```
