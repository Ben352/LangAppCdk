
def handler(event, context):
    claims = event["requestContext"]["authorizer"]["lambda"]
    return {
        "message": {
            "messageId": "m_4",
            "role": "assistant",
            "content": "Si dice 'stazione ferroviaria'.",
            "createdAt": "2026-03-14T15:43:01Z",
            "claims": claims
        }
        }
