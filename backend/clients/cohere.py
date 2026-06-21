# filepath: backend/clients/cohere.py
import cohere
from django.conf import settings


def call_cohere(
    system_prompt: str,
    user_message: str,
    force_json: bool = True,
    temperature: float = 0.3,
):
    client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)

    model = "command-r-plus-08-2024" if force_json else "command-a-reasoning-08-2025"

    kwargs = dict(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
    )

    if force_json:
        kwargs["response_format"] = {"type": "json_object"}
    else:
        kwargs["thinking"] = {"type": "enabled"}

    response = client.chat(**kwargs)
    content = response.message.content

    for block in content:
        if hasattr(block, "text") and block.type == "text":
            return block.text

    raise ValueError(f"No text block found in Cohere response. Content: {content}")