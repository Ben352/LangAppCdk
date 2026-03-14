def handler(event, context):
    claims = event["requestContext"]["authorizer"]["lambda"]
    return {
        "Conversations": [
            {"id": 1, "conversation": "text"},
            {"id": 2, "conversation": "text"}
        ],
        "claims": claims
    }
