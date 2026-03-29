import json
import logging
import os

import boto3
import firebase_admin
from botocore.exceptions import ClientError
from firebase_admin import auth, credentials

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TEST_BEARER_TOKEN = "Bearer superSecretKetUntilISetUpJWT"

_secrets_client = boto3.client("secretsmanager")
_firebase_app = None


def get_authorization_header(event: dict) -> str | None:
    headers = event.get("headers") or {}
    return headers.get("authorization") or headers.get("Authorization")


def extract_bearer_value(auth_header: str | None) -> str | None:
    if not auth_header:
        return None

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1].strip()


def load_firebase_service_account() -> dict:
    secret_arn = os.environ.get("FIREBASE_SECRET_ARN")
    if not secret_arn:
        raise RuntimeError("Missing FIREBASE_SECRET_ARN environment variable")

    response = _secrets_client.get_secret_value(SecretId=secret_arn)
    secret_string = response.get("SecretString")
    if not secret_string:
        raise RuntimeError("Firebase secret has no SecretString")

    return json.loads(secret_string)


def get_firebase_app():
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    service_account_info = load_firebase_service_account()
    cred = credentials.Certificate(service_account_info)
    _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def authorize_with_test_token(auth_header: str | None) -> dict | None:
    if auth_header == TEST_BEARER_TOKEN:
        logger.warning("Authorizer accepted request via TEST TOKEN bypass")
        return {
            "isAuthorized": True,
            "context": {
                "userId": "123",
                "authMode": "test-token",
            },
        }

    return None


def authorize_with_firebase(auth_header: str | None) -> dict | None:
    bearer_token = extract_bearer_value(auth_header)
    if not bearer_token:
        logger.info("No valid Bearer token format found for Firebase auth")
        return None

    try:
        get_firebase_app()
        decoded_token = auth.verify_id_token(bearer_token)
        uid = decoded_token["uid"]

        logger.info(
            "Authorizer accepted request via Firebase uid=%s email=%s",
            uid,
            decoded_token.get("email", ""),
        )

        return {
            "isAuthorized": True,
            "context": {
                "userId": uid,
                "authMode": "firebase",
                "email": str(decoded_token.get("email", "")),
            },
        }

    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token rejected: expired token")
        return None
    except auth.RevokedIdTokenError:
        logger.warning("Firebase token rejected: revoked token")
        return None
    except auth.InvalidIdTokenError:
        logger.warning("Firebase token rejected: invalid token")
        return None
    except ClientError as e:
        logger.exception("Failed to load Firebase secret from Secrets Manager: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected Firebase auth error: %s", e)
        return None


def handler(event, context):
    auth_header = get_authorization_header(event)

    # 1) Keep existing hardcoded testing token alive
    test_auth_result = authorize_with_test_token(auth_header)
    if test_auth_result is not None:
        return test_auth_result

    # 2) Shadow mode: also accept real Firebase auth
    firebase_auth_result = authorize_with_firebase(auth_header)
    if firebase_auth_result is not None:
        return firebase_auth_result

    logger.info("Authorization failed for request")
    return {
        "isAuthorized": False,
        "context": {
            "authMode": "none",
        },
    }