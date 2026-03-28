from litellm import completion


def generate_reply(
    system_prompt: str,
    messages: list[dict],
    api_key: str,
    provider_model: str = "claude-3-haiku-20240307",
    temperature: float = 0.7,
    max_tokens: int = 300,
) -> dict:
    llm_messages = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    result = completion(
        model=provider_model,
        messages=llm_messages,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return {
        "content": result.choices[0].message.content,
        "usage": {
            "prompt_tokens": getattr(result.usage, "prompt_tokens", None),
            "completion_tokens": getattr(result.usage, "completion_tokens", None),
            "total_tokens": getattr(result.usage, "total_tokens", None),
        },
    }