def handler(event, context):

    token = event["headers"].get("authorization")

    if token != "Bearer superSecretKetUntilISetUpJWT":
        return {
            "isAuthorized": False
        }

    return {
        "isAuthorized": True
    }