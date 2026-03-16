import json
import os

import boto3
from boto3.dynamodb.conditions import Key
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


def get_conversation_id(event: dict) -> str | None:
    return event.get("pathParameters", {}).get("conversationId")


def handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return response(401, {"message": "Unauthorized"})

        conversation_id = get_conversation_id(event)
        if not conversation_id:
            return response(400, {"message": "conversationId is required in path"})

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

        messages_result = table.query(
            KeyConditionExpression=Key("pk").eq(f"CONVERSATION#{conversation_id}")
        )

        raw_messages = messages_result.get("Items", [])

        messages = [
            {
                "messageId": item["messageId"],
                "role": item["role"],
                "content": item["content"],
                "createdAt": item["createdAt"]
            }
            for item in raw_messages
        ]

        return response(200, {
            "conversationId": conversation_item["conversationId"],
            "personaId": conversation_item["personaId"],
            "title": conversation_item["title"],
            "createdAt": conversation_item["createdAt"],
            "updatedAt": conversation_item.get("updatedAt"),
            "lastMessageAt": conversation_item.get("lastMessageAt"),
            "lastMessagePreview": conversation_item.get("lastMessagePreview"),
            "messages": messages
        })

    except ClientError as e:
        return response(500, {
            "message": "DynamoDB error",
            "error": e.response.get("Error", {}).get("Code", "UnknownError")
        })
    except Exception as e:
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })