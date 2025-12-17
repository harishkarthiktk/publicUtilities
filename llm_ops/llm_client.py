import requests
import time

# Configuration
CONFIG = {
    "ollama_model": "qwen3:latest",  # default Ollama model
    # "openrouter_model": (
    #     "mistralai/mistral-small-3.2-24b-instruct"
    # ),  # default OpenRouter model
    # "openrouter_model": "openai/gpt-5-nano",
    "openrouter_model": "google/gemma-3-4b-it",
    "ollama_host": "http://localhost:11434",
    "openrouter_base": "https://openrouter.ai/api/v1",
    "openrouter_timeout": 300,  # longer timeout for cloud API
    "max_retries": 3,  # for rate limit handling
    "max_workers": 5  # max concurrent API requests
}

# Hardcoded personas with system prompt templates
PERSONAS = {
    "summarizer": (
        "You are an expert summarizer. Provide a concise and accurate summary of the given "
        "content, highlighting the main points. The output should be markdown and do not "
        "return anything else or ask followup questions."
    ),
    "analyzer": (
        "You are an expert analyst. Analyze the key points, insights, and implications from "
        "the given content. The output should be markdown and do not return anything else "
        "or ask followup questions."
    ),
}


def call_llm_api(
    api_type,
    model,
    base_url_or_host,
    system_part,
    user_part,
    api_key=None,
    http_referer="",
    x_title="",
    timeout=120,
    max_retries=3,
    stop_event=None,
):
    """
    Make a single API call to Ollama or OpenRouter.
    For Ollama: /api/generate endpoint, compatible with version 0.12.9+.
    For OpenRouter: /chat/completions endpoint, OpenAI-compatible, with rate limit
    retry handling.
    """
    if api_type == "ollama":
        prompt = system_part + user_part
        url = f"{base_url_or_host}/api/generate"
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(url, json=data, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            return result["response"]
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Ollama API call failed: {e}")
        except KeyError:
            raise ValueError("Invalid response from Ollama API")
    elif api_type == "openrouter":
        if not api_key:
            raise ValueError(
                "OpenRouter API key is required. Provide it via --api-key or "
                "OPENROUTER_API_KEY env var."
            )
        url = f"{base_url_or_host}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if http_referer:
            headers["HTTP-Referer"] = http_referer
        if x_title:
            headers["X-Title"] = x_title
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_part},
                {"role": "user", "content": user_part}
            ],
            "stream": False
        }
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    url, headers=headers, json=data, timeout=timeout
                )
                if response.status_code == 429:  # Rate limit
                    if attempt < max_retries:
                        wait_time = (2 ** attempt) + 1  # Exponential backoff
                        if stop_event and stop_event.is_set():
                            raise KeyboardInterrupt(
                                "Interrupted during retry wait"
                            )
                        time.sleep(wait_time)
                        continue
                    else:
                        response.raise_for_status()
                else:
                    response.raise_for_status()
                result = response.json()
                if "choices" not in result or not result["choices"]:
                    raise ValueError(
                        "Invalid response structure from OpenRouter API"
                    )
                choice = result["choices"][0]
                if "message" not in choice:
                    raise ValueError("Invalid response from OpenRouter API")
                return choice["message"]["content"]
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    wait_time = (2 ** attempt) + 1
                    if stop_event and stop_event.is_set():
                        raise KeyboardInterrupt(
                            "Interrupted during retry wait"
                        )
                    time.sleep(wait_time)
                    continue
                raise ValueError(
                    f"OpenRouter API call failed after {max_retries} retries: {e}"
                )
    else:
        raise ValueError(f"Unsupported API type: {api_type}")


def build_prompt(persona_template, content, instructions=""):
    """
    Construct the system and user prompt parts: combine persona template, specific
    instructions, and file content.
    Returns (system_part, user_part) for flexible API formatting.
    """
    system_part = persona_template
    if instructions:
        system_part += f"\nSpecific instructions: {instructions}"
    user_part = f"\n\nContent to process:\n{content}"
    return system_part, user_part