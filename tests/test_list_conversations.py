import json
import os
from unittest.mock import patch

os.environ["CONVERSATIONS_TABLE_NAME"] = "test-conversations"

from lambda_functions.listConversations.app import handler


def make_event(user_id: str | None = "user-123"):
    event = {"requestContext": {"authorizer": {"lambda": {}}}}
    if user_id is not None:
        event["requestContext"]["authorizer"]["lambda"]["userId"] = user_id
    return event


@patch("lambda_functions.listConversations.app.table")
def test_unauthorized(mock_table):
    result = handler(make_event(user_id=None), None)

    assert result["statusCode"] == 401
    assert json.loads(result["body"])["message"] == "Unauthorized"
    mock_table.query.assert_not_called()


@patch("lambda_functions.listConversations.app.table")
def test_empty_list(mock_table):
    mock_table.query.return_value = {"Items": []}

    result = handler(make_event(), None)

    assert result["statusCode"] == 200
    assert json.loads(result["body"])["items"] == []


@patch("lambda_functions.listConversations.app.table")
def test_returns_conversations_sorted_by_updated_at(mock_table):
    mock_table.query.return_value = {
        "Items": [
            {
                "conversationId": "conv-old",
                "personaId": "italian-tutor",
                "title": "Older convo",
                "createdAt": "2026-03-01T10:00:00Z",
                "updatedAt": "2026-03-01T10:00:00Z",
                "lastMessageAt": "2026-03-01T10:00:00Z",
                "lastMessagePreview": "First message",
            },
            {
                "conversationId": "conv-new",
                "personaId": "italian-tutor",
                "title": "Newer convo",
                "createdAt": "2026-03-15T10:00:00Z",
                "updatedAt": "2026-03-15T10:00:00Z",
                "lastMessageAt": "2026-03-15T10:00:00Z",
                "lastMessagePreview": "Latest message",
            },
        ]
    }

    result = handler(make_event(), None)

    assert result["statusCode"] == 200
    items = json.loads(result["body"])["items"]
    assert len(items) == 2
    assert items[0]["conversationId"] == "conv-new"
    assert items[1]["conversationId"] == "conv-old"
