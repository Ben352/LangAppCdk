import json
import os
from unittest.mock import patch

# Set env var before importing the Lambda module
os.environ["CONVERSATIONS_TABLE_NAME"] = "test-table"

from lambda_functions.getConversation.app import handler


def make_event(
    user_id: str | None = "123",
    conversation_id: str | None = "conv-123",
):
    event = {
        "requestContext": {
            "authorizer": {
                "lambda": {}
            }
        },
        "pathParameters": {}
    }

    if user_id is not None:
        event["requestContext"]["authorizer"]["lambda"]["userId"] = user_id

    if conversation_id is not None:
        event["pathParameters"]["conversationId"] = conversation_id

    return event


@patch("lambda_functions.getConversation.app.table")
def test_get_conversation_success(mock_table):
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
            "updatedAt": "2026-03-15T14:20:00Z",
            "lastMessageAt": "2026-03-15T14:20:00Z",
            "lastMessagePreview": "Placeholder LLM Answer",
        }
    }

    mock_table.query.return_value = {
        "Items": [
            {
                "pk": "CONVERSATION#conv-123",
                "sk": "MESSAGE#2026-03-15T14:19:00Z#msg-1",
                "type": "message",
                "messageId": "msg-1",
                "role": "user",
                "content": "Hello",
                "createdAt": "2026-03-15T14:19:00Z",
            },
            {
                "pk": "CONVERSATION#conv-123",
                "sk": "MESSAGE#2026-03-15T14:20:00Z#msg-2",
                "type": "message",
                "messageId": "msg-2",
                "role": "assistant",
                "content": "Placeholder LLM Answer",
                "createdAt": "2026-03-15T14:20:00Z",
            },
        ]
    }

    event = make_event()

    result = handler(event, None)

    assert result["statusCode"] == 200

    body = json.loads(result["body"])
    assert body["conversationId"] == "conv-123"
    assert body["personaId"] == "italian-tutor"
    assert body["title"] == "Test convo"
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["role"] == "assistant"

    mock_table.get_item.assert_called_once()
    mock_table.query.assert_called_once()


@patch("lambda_functions.getConversation.app.table")
def test_get_conversation_unauthorized(mock_table):
    event = make_event(user_id=None)

    result = handler(event, None)

    assert result["statusCode"] == 401

    body = json.loads(result["body"])
    assert body["message"] == "Unauthorized"

    mock_table.get_item.assert_not_called()
    mock_table.query.assert_not_called()


@patch("lambda_functions.getConversation.app.table")
def test_get_conversation_not_found(mock_table):
    mock_table.get_item.return_value = {}

    event = make_event()

    result = handler(event, None)

    assert result["statusCode"] == 404

    body = json.loads(result["body"])
    assert body["message"] == "Conversation not found"

    mock_table.get_item.assert_called_once()
    mock_table.query.assert_not_called()