import json
import os
import sys
from decimal import Decimal
from unittest.mock import patch

from botocore.exceptions import ClientError

os.environ["CONVERSATIONS_TABLE_NAME"] = "test-conversations"
os.environ["PROMPT_TABLE_NAME"] = "test-prompts"
os.environ["USER_METADATA_TABLE_NAME"] = "test-user-metadata"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

# llm_client.py is colocated with app.py in the Lambda package dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambda_functions", "sendMessage"))

from lambda_functions.sendMessage.app import handler


FAKE_CONVERSATION = {
    "pk": "USER#user-123",
    "sk": "CONVERSATION#conv-123",
    "type": "conversation",
    "userId": "user-123",
    "conversationId": "conv-123",
    "personaId": "italian-tutor",
    "title": "Test convo",
    "createdAt": "2026-03-15T14:17:16Z",
    "updatedAt": "2026-03-15T14:17:16Z",
    "lastMessageAt": "2026-03-15T14:17:16Z",
    "lastMessagePreview": "",
}

FAKE_PERSONA = {
    "pk": "PROMPT#italian-tutor",
    "sk": "VERSION#1",
    "systemPrompt": "You are an Italian tutor.",
    "starterMessage": "Ciao!",
    "providerModel": "anthropic/claude-haiku-4-5-20251001",
    "temperature": Decimal("0.7"),
    "maxTokens": Decimal("1000"),
}

FAKE_USER_METADATA = {
    "pk": "USER#user-123",
    "sk": "METADATA",
    "userId": "user-123",
    "isActivated": True,
    "tokenBudgetTotal": Decimal("100000"),
    "tokensUsed": Decimal("0"),
}

FAKE_LLM_RESULT = {
    "content": "Ciao! Come stai?",
    "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
}


def make_event(
    user_id: str | None = "user-123",
    conversation_id: str | None = "conv-123",
    content: str = "Hello",
):
    event = {
        "requestContext": {"authorizer": {"lambda": {}}},
        "pathParameters": {},
        "body": json.dumps({"content": content}),
    }
    if user_id is not None:
        event["requestContext"]["authorizer"]["lambda"]["userId"] = user_id
    if conversation_id is not None:
        event["pathParameters"]["conversationId"] = conversation_id
    return event


@patch("lambda_functions.sendMessage.app.table")
def test_unauthorized(mock_table):
    result = handler(make_event(user_id=None), None)

    assert result["statusCode"] == 401
    assert json.loads(result["body"])["message"] == "Unauthorized"
    mock_table.get_item.assert_not_called()


@patch("lambda_functions.sendMessage.app.table")
def test_missing_content(mock_table):
    result = handler(make_event(content=""), None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["message"] == "content is required"
    mock_table.get_item.assert_not_called()


@patch("lambda_functions.sendMessage.app.table")
def test_conversation_not_found(mock_table):
    mock_table.get_item.return_value = {}

    result = handler(make_event(), None)

    assert result["statusCode"] == 404
    assert json.loads(result["body"])["message"] == "Conversation not found"


@patch("lambda_functions.sendMessage.app.user_metadata_table")
@patch("lambda_functions.sendMessage.app.prompt_table")
@patch("lambda_functions.sendMessage.app.table")
def test_account_not_activated(mock_table, mock_prompt_table, mock_user_metadata_table):
    mock_table.get_item.return_value = {"Item": FAKE_CONVERSATION}
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}
    mock_user_metadata_table.get_item.return_value = {
        "Item": {**FAKE_USER_METADATA, "isActivated": False}
    }

    result = handler(make_event(), None)

    assert result["statusCode"] == 403
    assert json.loads(result["body"])["message"] == "Account not activated"


@patch("lambda_functions.sendMessage.app.user_metadata_table")
@patch("lambda_functions.sendMessage.app.prompt_table")
@patch("lambda_functions.sendMessage.app.table")
def test_token_budget_exceeded(mock_table, mock_prompt_table, mock_user_metadata_table):
    mock_table.get_item.return_value = {"Item": FAKE_CONVERSATION}
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}
    # 99500 used, 100000 total → 500 remaining < 1000 max_tokens.
    # The reservation is an atomic conditional update, so DynamoDB itself
    # rejects it rather than Python comparing stale get_item values.
    mock_user_metadata_table.get_item.return_value = {
        "Item": {**FAKE_USER_METADATA, "tokensUsed": Decimal("99500")}
    }
    mock_user_metadata_table.update_item.side_effect = ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException", "Message": "check failed"}},
        "UpdateItem",
    )

    result = handler(make_event(), None)

    assert result["statusCode"] == 429
    assert json.loads(result["body"])["message"] == "Token budget exceeded"
    mock_table.put_item.assert_not_called()


@patch("lambda_functions.sendMessage.app.user_metadata_table")
@patch("lambda_functions.sendMessage.app.prompt_table")
@patch("lambda_functions.sendMessage.app.table")
def test_user_metadata_missing(mock_table, mock_prompt_table, mock_user_metadata_table):
    mock_table.get_item.return_value = {"Item": FAKE_CONVERSATION}
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}
    mock_user_metadata_table.get_item.return_value = {}

    result = handler(make_event(), None)

    assert result["statusCode"] == 500


@patch("lambda_functions.sendMessage.app.generate_reply")
@patch("lambda_functions.sendMessage.app.get_claude_api_key")
@patch("lambda_functions.sendMessage.app.user_metadata_table")
@patch("lambda_functions.sendMessage.app.prompt_table")
@patch("lambda_functions.sendMessage.app.table")
def test_happy_path(mock_table, mock_prompt_table, mock_user_metadata_table, mock_get_api_key, mock_generate_reply):
    mock_table.get_item.return_value = {"Item": FAKE_CONVERSATION}
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}
    mock_user_metadata_table.get_item.return_value = {"Item": FAKE_USER_METADATA}
    mock_table.query.return_value = {"Items": []}
    mock_get_api_key.return_value = "fake-api-key"
    mock_generate_reply.return_value = FAKE_LLM_RESULT

    result = handler(make_event(), None)

    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["conversationId"] == "conv-123"
    assert body["userMessage"]["role"] == "user"
    assert body["userMessage"]["content"] == "Hello"
    assert body["assistantMessage"]["role"] == "assistant"
    assert body["assistantMessage"]["content"] == "Ciao! Come stai?"
    assert body["usage"]["total_tokens"] == 150

    assert mock_table.put_item.call_count == 2
    mock_table.update_item.assert_called_once()

    # One atomic write to reserve max_tokens (1000) up front, one to true
    # up the ledger to the 150 tokens actually consumed.
    assert mock_user_metadata_table.update_item.call_count == 2
    reserve_call, reconcile_call = mock_user_metadata_table.update_item.call_args_list
    assert reserve_call.kwargs["ExpressionAttributeValues"][":max_tokens"] == 1000
    assert reconcile_call.kwargs["ExpressionAttributeValues"][":adjustment"] == -850


@patch("lambda_functions.sendMessage.app.user_metadata_table")
@patch("lambda_functions.sendMessage.app.prompt_table")
@patch("lambda_functions.sendMessage.app.table")
def test_reserve_token_budget_race_is_atomic(mock_table, mock_prompt_table, mock_user_metadata_table):
    """Two concurrent requests both read the same stale tokensUsed, but only
    one may win the atomic conditional reservation; the loser gets 429
    without having called the LLM or persisted any messages."""
    mock_table.get_item.return_value = {"Item": FAKE_CONVERSATION}
    mock_prompt_table.get_item.return_value = {"Item": FAKE_PERSONA}
    # Both requests see the same pre-race snapshot: 99200 used, 100000
    # total → 800 remaining, enough for one 1000-max_tokens reservation
    # but not two.
    mock_user_metadata_table.get_item.return_value = {
        "Item": {**FAKE_USER_METADATA, "tokensUsed": Decimal("99200")}
    }
    mock_user_metadata_table.update_item.side_effect = [
        None,  # first request's reservation succeeds
        ClientError(
            {"Error": {"Code": "ConditionalCheckFailedException", "Message": "check failed"}},
            "UpdateItem",
        ),  # second request's reservation is rejected atomically
    ]

    first_result = handler(make_event(), None)
    second_result = handler(make_event(), None)

    assert first_result["statusCode"] != 429
    assert second_result["statusCode"] == 429
    assert json.loads(second_result["body"])["message"] == "Token budget exceeded"
