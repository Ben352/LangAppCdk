import os

import pytest

from lambda_functions.sendMessage.llm_client import generate_reply


pytestmark = pytest.mark.integration


def test_generate_reply_real_provider():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    result = generate_reply(
        system_prompt=(
            "This is a unit connection test. "
            "Reply with exactly LITELLM_CONNECTION_OK and nothing else."
        ),
        messages=[
            {
                "role": "user",
                "content": "Return the exact required test string."
            }
        ],
        api_key=api_key,
        temperature=0.0,
        max_tokens=20,
    )

    content = result["content"].strip()

    assert "LITELLM_CONNECTION_OK" in content
    assert result["usage"]["total_tokens"] is not None