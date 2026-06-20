import cohere
from django.conf import settings


def call_cohere(
    system_prompt: str,
    user_message: str,
    force_json: bool = True,
    temperature: float = 0.3,
):
    client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
    kwargs = dict(
        model="command-a-reasoning-08-2025",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        thinking={"type": "enabled"},
        temperature=temperature,
    )
    if force_json:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat(**kwargs)
    response = response.message.content[1].text
    return response
