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


def handler(event, context):
    try:
        user_id = get_user_id(event)
        if not user_id:
            return response(401, {"message": "Unauthorized"})

        result = table.query(
            KeyConditionExpression=(
                Key("pk").eq(f"USER#{user_id}") &
                Key("sk").begins_with("CONVERSATION#")
            )
        )

        items = result.get("Items", [])

        conversations = [
            {
                "conversationId": item["conversationId"],
                "personaId": item["personaId"],
                "title": item["title"],
                "createdAt": item["createdAt"],
                "updatedAt": item.get("updatedAt", item["createdAt"]),
                "lastMessageAt": item.get("lastMessageAt"),
                "lastMessagePreview": item.get("lastMessagePreview", "")
            }
            for item in items
        ]

        conversations.sort(
            key=lambda x: x.get("updatedAt") or x["createdAt"],
            reverse=True
        )

        return response(200, {
            "items": conversations
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