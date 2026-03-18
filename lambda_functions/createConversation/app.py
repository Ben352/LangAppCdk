import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["CONVERSATIONS_TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def get_user_id(event: dict) -> str | None:
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("lambda", {})
        .get("userId")
    )


def handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return response(401, {"message": "Unauthorized"})

        body = json.loads(event.get("body") or "{}")

        persona_id = body.get("personaId")
        title = body.get("title", "").strip()

        if not persona_id:
            return response(400, {"message": "personaId is required"})

        if not title:
            title = "New conversation"

        conversation_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        item = {
            "pk": f"USER#{user_id}",
            "sk": f"CONVERSATION#{conversation_id}",
            "type": "conversation",
            "userId": user_id,
            "conversationId": conversation_id,
            "personaId": persona_id,
            "title": title,
            "createdAt": created_at,
            "updatedAt": created_at,
            "lastMessageAt": created_at,
            "lastMessagePreview": ""
        }

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)"
        )

        return response(201, {
            "conversationId": conversation_id,
            "personaId": persona_id,
            "title": title,
            "createdAt": created_at
        })

    except ClientError as e:
        return response(500, {
            "message": "Failed to create conversation",
            "error": e.response.get("Error", {}).get("Code", "UnknownError")
        })
    except Exception as e:
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })