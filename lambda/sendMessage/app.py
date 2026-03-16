import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

TABLE_NAME = os.environ["CONVERSATIONS_TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

## To do: - add validation using the metadata label


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


def get_user_id(event: dict) -> str | None:
    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("lambda", {})
        .get("userId")
    )


def get_conversation_id(event: dict) -> str | None:
    return event.get("pathParameters", {}).get("conversationId")


def get_body(event: dict) -> dict:
    raw_body = event.get("body") or "{}"
    return json.loads(raw_body)


def handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return response(401, {"message": "Unauthorized"})

        conversation_id = get_conversation_id(event)
        if not conversation_id:
            return response(400, {"message": "conversationId is required in path"})

        body = get_body(event)
        content = (body.get("content") or "").strip()

        if not content:
            return response(400, {"message": "content is required"})

        # 1. Verify the conversation exists and belongs to the user
        conversation_pk = f"USER#{user_id}"
        conversation_sk = f"CONVERSATION#{conversation_id}"

        conversation_result = table.get_item(
            Key={
                "pk": conversation_pk,
                "sk": conversation_sk
            }
        )

        conversation_item = conversation_result.get("Item")
        if not conversation_item:
            return response(404, {"message": "Conversation not found"})

        # 2. Create the user message
        user_message_id = str(uuid.uuid4())
        user_created_at = now_iso()

        user_message_item = {
            "pk": f"CONVERSATION#{conversation_id}",
            "sk": f"MESSAGE#{user_created_at}#{user_message_id}",
            "type": "message",
            "userId": user_id,
            "conversationId": conversation_id,
            "messageId": user_message_id,
            "role": "user",
            "content": content,
            "createdAt": user_created_at
        }

        table.put_item(Item=user_message_item)

        # 3. Simulate LLM response
        assistant_content = "Placeholder LLM Answer"

        # 4. Create the assistant message
        assistant_message_id = str(uuid.uuid4())
        assistant_created_at = now_iso()

        assistant_message_item = {
            "pk": f"CONVERSATION#{conversation_id}",
            "sk": f"MESSAGE#{assistant_created_at}#{assistant_message_id}",
            "type": "message",
            "userId": user_id,
            "conversationId": conversation_id,
            "messageId": assistant_message_id,
            "role": "assistant",
            "content": assistant_content,
            "createdAt": assistant_created_at
        }

        table.put_item(Item=assistant_message_item)

        # 5. Update conversation metadata
        table.update_item(
            Key={
                "pk": conversation_pk,
                "sk": conversation_sk
            },
            UpdateExpression="""
                SET updatedAt = :updatedAt,
                    lastMessageAt = :lastMessageAt,
                    lastMessagePreview = :lastMessagePreview
            """,
            ExpressionAttributeValues={
                ":updatedAt": assistant_created_at,
                ":lastMessageAt": assistant_created_at,
                ":lastMessagePreview": assistant_content
            }
        )

        return response(201, {
            "conversationId": conversation_id,
            "userMessage": {
                "messageId": user_message_id,
                "role": "user",
                "content": content,
                "createdAt": user_created_at
            },
            "assistantMessage": {
                "messageId": assistant_message_id,
                "role": "assistant",
                "content": assistant_content,
                "createdAt": assistant_created_at
            }
        })

    except ClientError as e:
        return response(500, {
            "message": "DynamoDB error",
            "error": e.response.get("Error", {}).get("Code", "UnknownError")
        })
    except json.JSONDecodeError:
        return response(400, {
            "message": "Invalid JSON body"
        })
    except Exception as e:
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })