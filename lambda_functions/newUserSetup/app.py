import json
import os
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["USER_METADATA_TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
_secrets_client = boto3.client("secretsmanager")


def load_secret_key() -> str:
    secret_id = os.environ.get("FIREBASE_SYNC_KEY")
    if not secret_id:
        raise RuntimeError("Missing FIREBASE_SYNC_KEY environment variable")

    response = _secrets_client.get_secret_value(SecretId=secret_id)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("Firebase secret has no SecretString")

    secret_json = json.loads(secret_string)

    # expects secret like: {"key":"super-secret-value"}
    secret_value = secret_json.get("key")
    if not secret_value:
        raise RuntimeError('Firebase secret JSON must contain a "key" field')

    return secret_value


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def handler(event, context):
    try:
        internal_secret = load_secret_key()

        headers = event.get("headers") or {}
        provided_secret = (
            headers.get("x-internal-secret")
            or headers.get("X-Internal-Secret")
        )

        if provided_secret != internal_secret:
            return response(403, {"message": "Forbidden"})

        body = json.loads(event.get("body") or "{}")

        user_id = (body.get("userId") or "").strip()
        name = (body.get("name") or "").strip()
        email = (body.get("email") or "").strip()
        auth_provider = (body.get("authProvider") or "").strip()

        if not user_id:
            return response(400, {"message": "userId is required"})
        if not email:
            return response(400, {"message": "email is required"})
        if not auth_provider:
            return response(400, {"message": "authProvider is required"})

        now = now_iso()

        table.update_item(
            Key={
                "pk": f"USER#{user_id}",
                "sk": "METADATA"
            },
            UpdateExpression="""
                SET userId = :userId,
                    #name = :name,
                    email = :email,
                    authProvider = :authProvider,
                    updatedAt = :updatedAt,
                    createdAt = if_not_exists(createdAt, :createdAt),
                    isActivated = if_not_exists(isActivated, :isActivated)
            """,
            ExpressionAttributeNames={
                "#name": "name"
            },
            ExpressionAttributeValues={
                ":userId": user_id,
                ":name": name,
                ":email": email,
                ":authProvider": auth_provider,
                ":updatedAt": now,
                ":createdAt": now,
                ":isActivated": False
            }
        )

        return response(200, {
            "message": "User metadata synced",
            "userId": user_id
        })

    except ClientError as e:
        return response(500, {
            "message": "DynamoDB error",
            "error": e.response.get("Error", {}).get("Code", "UnknownError")
        })
    except json.JSONDecodeError:
        return response(400, {"message": "Invalid JSON body"})
    except Exception as e:
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })