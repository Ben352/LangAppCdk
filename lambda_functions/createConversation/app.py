import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError
from personas import get_persona

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


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return response(401, {"message": "Unauthorized"})

        body = json.loads(event.get("body") or "{}")

        persona_id = body.get("personaId")
        if not persona_id:
            return response(400, {"message": "personaId is required"})

        persona = get_persona(persona_id=persona_id)
        starter_message = persona.get("starter_message", "Ciao! Come stai?")

        title = body.get("title", "").strip()
        if not title:
            title = "New conversation"

        conversation_id = str(uuid.uuid4())
        created_at = now_iso()

        # 1. Create conversation metadata item
        conversation_item = {
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
            "lastMessagePreview": starter_message
        }

        table.put_item(
            Item=conversation_item,
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)"
        )

        # 2. Create initial assistant message item
        assistant_message_id = str(uuid.uuid4())
        assistant_message_item = {
            "pk": f"CONVERSATION#{conversation_id}",
            "sk": f"MESSAGE#{created_at}#{assistant_message_id}",
            "type": "message",
            "userId": user_id,
            "conversationId": conversation_id,
            "messageId": assistant_message_id,
            "role": "assistant",
            "content": starter_message,
            "createdAt": created_at
        }

        table.put_item(Item=assistant_message_item)

        # 3. Return the created conversation plus first message
        return response(201, {
            "conversationId": conversation_id,
            "personaId": persona_id,
            "title": title,
            "createdAt": created_at,
            "assistantMessage": {
                "messageId": assistant_message_id,
                "role": "assistant",
                "content": starter_message,
                "createdAt": created_at
            }
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