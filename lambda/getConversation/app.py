
def handler(event, context):
    claims = event["requestContext"]["authorizer"]["lambda"]
    return {
        "conversationId": "c_123",
        "personaId": "italian-tutor",
        "title": "Italian restaurant practice",
        "createdAt": "2026-03-14T15:40:00Z",
        "messages": [
            {
                "messageId": "m_1",
                "role": "user",
                "content": "Ciao, vorrei ordinare un caffè.",
                "createdAt": "2026-03-14T15:40:10Z"
            },
            {
                "messageId": "m_2",
                "role": "assistant",
                "content": "Certo! Vuoi anche qualcosa da mangiare?",
                "createdAt": "2026-03-14T15:40:12Z",
                "claims": claims
            }
        ]
    }
