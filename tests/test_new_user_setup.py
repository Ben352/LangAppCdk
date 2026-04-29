import json
import os
from unittest.mock import patch

os.environ["USER_METADATA_TABLE_NAME"] = "test-user-metadata"
os.environ["FIREBASE_SYNC_KEY"] = "test-firebase-sync-key"

from lambda_functions.newUserSetup.app import handler


CORRECT_SECRET = "super-secret-key"


def make_event(
    secret: str | None = CORRECT_SECRET,
    body: dict | None = None,
):
    if body is None:
        body = {
            "userId": "user-123",
            "name": "John",
            "email": "john@example.com",
            "authProvider": "google",
        }
    event = {
        "headers": {},
        "body": json.dumps(body),
    }
    if secret is not None:
        event["headers"]["x-internal-secret"] = secret
    return event


@patch("lambda_functions.newUserSetup.app.load_secret_key")
@patch("lambda_functions.newUserSetup.app.table")
def test_wrong_secret(mock_table, mock_load_secret_key):
    mock_load_secret_key.return_value = CORRECT_SECRET

    result = handler(make_event(secret="wrong-secret"), None)

    assert result["statusCode"] == 403
    assert json.loads(result["body"])["message"] == "Forbidden"
    mock_table.update_item.assert_not_called()


@patch("lambda_functions.newUserSetup.app.load_secret_key")
@patch("lambda_functions.newUserSetup.app.table")
def test_missing_user_id(mock_table, mock_load_secret_key):
    mock_load_secret_key.return_value = CORRECT_SECRET

    result = handler(make_event(body={"email": "john@example.com", "authProvider": "google"}), None)

    assert result["statusCode"] == 400
    assert json.loads(result["body"])["message"] == "userId is required"
    mock_table.update_item.assert_not_called()


@patch("lambda_functions.newUserSetup.app.load_secret_key")
@patch("lambda_functions.newUserSetup.app.table")
def test_happy_path(mock_table, mock_load_secret_key):
    mock_load_secret_key.return_value = CORRECT_SECRET

    result = handler(make_event(), None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["userId"] == "user-123"

    mock_table.update_item.assert_called_once()
    expr_values = mock_table.update_item.call_args.kwargs["ExpressionAttributeValues"]
    assert expr_values[":tokenBudgetTotal"] == 100000
    assert expr_values[":tokensUsed"] == 0
    assert expr_values[":isActivated"] is False
