PERSONAS = {
    "italian-tutor": {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "system_prompt": "You are a helpful Italian tutor."
    }
}


def get_persona(persona_id: str) -> dict:
    persona = PERSONAS.get(persona_id)
    if not persona:
        raise ValueError(f"Unknown persona: {persona_id}")
    return persona