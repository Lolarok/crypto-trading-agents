"""LLM client factory — supports OpenAI, Anthropic, Google, OpenRouter."""

from typing import Optional


def create_llm(provider: str, model: str, base_url: Optional[str] = None, **kwargs):
    """
    Create an LLM instance based on the provider.

    Args:
        provider: "openai", "anthropic", "google", or "openrouter"
        model: Model name
        base_url: Optional custom API base URL
        **kwargs: Additional provider-specific kwargs
    """
    provider = provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        params = {"model": model, "temperature": 0.3}
        if base_url:
            params["base_url"] = base_url
        if kwargs.get("reasoning_effort"):
            params["reasoning_effort"] = kwargs["reasoning_effort"]
        return ChatOpenAI(**params)

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        params = {"model": model, "temperature": 0.3}
        if kwargs.get("effort"):
            params["thinking"] = {"type": "enabled", "budget_tokens": 4096}
        return ChatAnthropic(**params)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        params = {"model": model, "temperature": 0.3}
        if kwargs.get("thinking_level"):
            params["thinking_level"] = kwargs["thinking_level"]
        return ChatGoogleGenerativeAI(**params)

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        params = {
            "model": model,
            "temperature": 0.3,
            "base_url": "https://openrouter.ai/api/v1",
        }
        if base_url:
            params["base_url"] = base_url
        return ChatOpenAI(**params)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
