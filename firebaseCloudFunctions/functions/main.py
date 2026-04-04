from firebase_functions import identity_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
import urllib.request
import json
import os

set_global_options(max_instances=2)
initialize_app()

AWS_LAMBDA_URL = os.environ.get("AWS_LAMBDA_URL")
API_SECRET = os.environ.get("API_SECRET")

@identity_fn.before_user_created()
def sync_user_to_backend(event: identity_fn.AuthBlockingEvent) -> identity_fn.BeforeCreateResponse | None:
    user = event.data

    provider_data = user.provider_data or []
    
    payload = {
        "userId": user.uid,                          # was "uid"
        "name": provider_data[0].display_name if provider_data else None,  # was "display_name"
        "email": user.email,
        "authProvider": provider_data[0].provider_id if provider_data else None,  # was "provider_id"
        "photo_url": user.photo_url,
        "phone_number": user.phone_number,
        "email_verified": user.email_verified,
        "provider_data": [
            {
                "uid": p.uid,
                "email": p.email,
                "display_name": p.display_name,
                "provider_id": p.provider_id,
            }
            for p in provider_data
        ],
    }

    try:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            AWS_LAMBDA_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-internal-secret": API_SECRET,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"Lambda responded with status {response.status} for user {user.uid}")
    except Exception as e:
        print(f"Failed to notify backend: {e}")

    return None