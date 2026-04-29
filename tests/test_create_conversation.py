import json
import os
from unittest.mock import patch

os.environ["CONVERSATIONS_TABLE_NAME"] = "test-conversations"
os.environ["PROMPT_TABLE_NAME"] = "test-prompts"

from lambda_functions.createConversation.app import handler


FAKE_PERSONA = {
    "pk": "PROMPT#italian-tutor",
    "sk": "VERSION#1",
    "systemPrompt": "You are an Italian tutor.",
    "starterMessage": "Ciao! Come ti chiami?",
    "providerModel": "anthropic/claude-haiku-4-5-20251001",
    "temperature": "0.7",
    "maxTokens": "1000",
}


def make_event(
    user_id: str | None = "user-123",
    body: dict | None = None,
):
    if body is None:
        body = {"personaId": "italian-tutor", "title": "Test convo"}
    event = {
        "requestContext": {"authorizer": {"lambda": {}}},
        "body": json.dumps(body),
    }
    if user_id is not None:
        event["requestContext"]["authorizer"]["lambda"]["userId"] = user_id
    return event


@patch("lambda_functions.createConversation.app.prompt_table")
@patch("lambda_functions.createConversation.app.table")
def test_unauthorized(mock_table, mock_prompt_table):
    result = handler(make_event(user_id=None), None)

    assert result["statusCode"] == 401
    assert json.loads(result["body"])["message"] == "Unauthorized"
    mock_table.put_item.assert_not_called()


@patch("lambda_functions.createConversation.app.prompt_table")
@patch("lambda_functions.createConversation.app.table")
def test_unknown_persona_id(mock_table, mock_prompt_table):
    mock_prompt_table.get_item.return_value = {}

    result = handler(make_event(body={"personaId": "nonexistent-persona", "title": "Test"}), None)

    assert result["statusCode"] == 400
    assert "nonexistent-persona" in json.loads(result["body"])["message"]
    mock_table.put_item.assert_not_called()


@patch("lambda_functions.createConversation.app.prompt_table")
@patch("lambda_functions.createConversation.app.table")
def test_happy_path(mock_table, mock_prompt_table):
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}

    result = handler(make_event(), None)

    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert "conversationId" in body
    assert body["personaId"] == "italian-tutor"
    assert body["title"] == "Test convo"
    assert body["assistantMessage"]["role"] == "assistant"
    assert body["assistantMessage"]["content"] == "Ciao! Come ti chiami?"

    assert mock_table.put_item.call_count == 2
