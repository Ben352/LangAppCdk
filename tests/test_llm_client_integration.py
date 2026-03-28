import os

import pytest

from lambda_functions.shared.llm_client import generate_reply


pytestmark = pytest.mark.integration


def test_generate_reply_real_provider():
    if not os.getenv("ANTHROPIC_API_KEY"):
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
        temperature=0.0,
        max_tokens=20,
    )

    content = result["content"].strip()

    assert "LITELLM_CONNECTION_OK" in content
    assert result["usage"]["total_tokens"] is not None