import json
import os
from unittest.mock import patch

os.environ["CONVERSATIONS_TABLE_NAME"] = "test-table"

from lambda_functions.sendMessage.app import handler


def make_event(
    user_id: str | None = "123",
    conversation_id: str | None = "conv-123",
    content: str = "Hello",
):
    event = {
        "requestContext": {
            "authorizer": {
                "lambda": {}
            }
        },
        "pathParameters": {},
        "body": json.dumps({"content": content}),
    }

    if user_id is not None:
        event["requestContext"]["authorizer"]["lambda"]["userId"] = user_id

    if conversation_id is not None:
        event["pathParameters"]["conversationId"] = conversation_id

    return event


@patch("lambda_functions.sendMessage.app.get_persona")
@patch("lambda_functions.sendMessage.app.table")
def test_send_message_can_access_persona(mock_table, mock_get_persona):
    mock_table.get_item.return_value = {
        "Item": {
            "pk": "USER#123",
            "sk": "CONVERSATION#conv-123",
            "type": "conversation",
            "userId": "123",
            "conversationId": "conv-123",
            "personaId": "italian-tutor",
            "title": "Test convo",
            "createdAt": "2026-03-15T14:17:16Z",
            "updatedAt": "2026-03-15T14:17:16Z",
            "lastMessageAt": "2026-03-15T14:17:16Z",
            "lastMessagePreview": ""
        }
    }

    mock_get_persona.return_value = {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "system_prompt": "You are a helpful Italian tutor."
    }

    event = make_event(
        user_id="123",
        conversation_id="conv-123",
        content="Hello"
    )

    result = handler(event, None)

    assert result["statusCode"] == 201

    mock_get_persona.assert_called_once_with("italian-tutor")

    body = json.loads(result["body"])
    assert body["conversationId"] == "conv-123"
    assert body["userMessage"]["role"] == "user"
    assert body["assistantMessage"]["role"] == "assistant"

    assert mock_table.get_item.called
    assert mock_table.put_item.call_count == 2
    assert mock_table.update_item.called