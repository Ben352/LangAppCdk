import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from llm_client import generate_reply

TABLE_NAME = os.environ["CONVERSATIONS_TABLE_NAME"]
PROMPT_TABLE_NAME = os.environ["PROMPT_TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
prompt_table = dynamodb.Table(PROMPT_TABLE_NAME)
secrets_client = boto3.client("secretsmanager")


def get_claude_api_key() -> str:
    secret_id = os.environ["ANTHROPIC_API_KEY"]
    response = secrets_client.get_secret_value(SecretId=secret_id)
    return response["SecretString"]


def response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def to_python_number(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    return value


def get_persona_from_ddb(persona_id: str) -> dict | None:
    result = prompt_table.get_item(
        Key={
            "pk": f"PROMPT#{persona_id}",
            "sk": "VERSION#1",
        }
    )
    return result.get("Item")


def get_last_messages(conversation_id: str, limit: int = 4):
    result = table.query(
        KeyConditionExpression=(
            Key("pk").eq(f"CONVERSATION#{conversation_id}") &
            Key("sk").begins_with("MESSAGE#")
        ),
        ScanIndexForward=False,
        Limit=limit
    )

    items = result.get("Items", [])
    items.reverse()

    return [
        {
            "messageId": item["messageId"],
            "role": item["role"],
            "content": item["content"],
            "createdAt": item["createdAt"]
        }
        for item in items
    ]


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

        persona_id = conversation_item["personaId"]
        persona = get_persona_from_ddb(persona_id)
        if not persona:
            return response(500, {"message": f"Persona config not found for {persona_id}"})

        system_prompt = persona["systemPrompt"]
        provider_model = persona["providerModel"]
        temperature = to_python_number(persona["temperature"])
        max_tokens = to_python_number(persona["maxTokens"])

        last_messages = get_last_messages(conversation_id, limit=4)
        api_key = get_claude_api_key()

        llm_messages = [
            *last_messages,
            {"role": "user", "content": content},
        ]

        llm_result = generate_reply(
            system_prompt=system_prompt,
            messages=llm_messages,
            api_key=api_key,
            provider_model=provider_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        assistant_content = llm_result["content"]

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
            },
            "usage": llm_result["usage"]
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
    except KeyError as e:
        return response(500, {
            "message": "Persona config is missing a required field",
            "error": str(e)
        })
    except Exception as e:
        return response(500, {
            "message": "Internal server error",
            "error": str(e)
        })