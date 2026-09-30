from types import SimpleNamespace
from unittest.mock import patch

from lambda_functions.sendMessage.llm_client import generate_reply


def make_fake_completion_result(content="Ciao!", prompt_tokens=10, completion_tokens=5, total_tokens=15):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


@patch("lambda_functions.sendMessage.llm_client.completion")
def test_generate_reply_builds_system_message_and_shapes_result(mock_completion):
    mock_completion.return_value = make_fake_completion_result()

    result = generate_reply(
        system_prompt="You are an Italian tutor.",
        messages=[{"role": "user", "content": "Ciao"}],
        api_key="fake-key",
        provider_model="anthropic/claude-haiku-4-5-20251001",
        temperature=0.5,
        max_tokens=200,
    )

    mock_completion.assert_called_once_with(
        model="anthropic/claude-haiku-4-5-20251001",
        messages=[
            {"role": "system", "content": "You are an Italian tutor."},
            {"role": "user", "content": "Ciao"},
        ],
        api_key="fake-key",
        temperature=0.5,
        max_tokens=200,
    )
    assert result == {
        "content": "Ciao!",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


@patch("lambda_functions.sendMessage.llm_client.completion")
def test_generate_reply_default_provider_model_has_litellm_prefix(mock_completion):
    # Regression guard: litellm requires a "<provider>/<model>" string, and
    # this default previously lacked the "anthropic/" prefix, which only
    # surfaced when something forgot to pass provider_model explicitly.
    mock_completion.return_value = make_fake_completion_result()

    generate_reply(
        system_prompt="sys",
        messages=[],
        api_key="fake-key",
    )

    called_model = mock_completion.call_args.kwargs["model"]
    assert called_model.startswith("anthropic/")
