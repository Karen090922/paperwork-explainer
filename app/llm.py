"""Creates the AI model the app talks to, using the settings in your .env file.

Every other file calls get_model() instead of creating a model itself, so you can
switch between Google, Anthropic and OpenAI by changing one line in .env.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

# Reads .env and puts its values into os.environ. Real environment variables win.
load_dotenv()

DEFAULT_MODELS = {
    "google_genai": "gemini-3.8-flash",
    "anthropic": "claude-haiku-5-5",
    "openai": "gpt-5-mini",
}

API_KEY_NAMES = {
    "google_genai": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class ConfigError(RuntimeError):
    """Something is missing or wrong in .env. The message says how to fix it."""


def get_model() -> BaseChatModel:
    """Return the chat model chosen in .env, ready to call."""
    provider = os.getenv("LLM_PROVIDER", "google_genai").strip()
    if provider not in DEFAULT_MODELS:
        choices = ", ".join(DEFAULT_MODELS)
        raise ConfigError(f"LLM_PROVIDER in .env is '{provider}'. Use one of: {choices}.")

    key_name = API_KEY_NAMES[provider]
    if not os.getenv(key_name, "").strip():
        raise ConfigError(
            f"{key_name} is empty. Copy .env.example to .env and paste your API key there."
        )

    model_name = os.getenv("LLM_MODEL", "").strip() or DEFAULT_MODELS[provider]

    # The plan says "temperature 0", but newer models (Gemini 3.8 Flash, Claude Haiku 5.5)
    # ignore or reject it. So it's only sent when you set LLM_TEMPERATURE yourself.
    # Consistent answers come from the strict prompt, structured output and your evals.
    extra = {}
    temperature = os.getenv("LLM_TEMPERATURE", "").strip()
    if temperature:
        extra["temperature"] = float(temperature)

    return init_chat_model(model_name, model_provider=provider, timeout=60, max_retries=1, **extra)
