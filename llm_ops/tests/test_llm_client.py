import pytest
from unittest.mock import patch, MagicMock
import requests

from llm_client import call_llm_api


def test_call_llm_api_ollama_success():
    """Test successful Ollama API call."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "mock summary"}
        mock_post.return_value = mock_response

        system_part = "You are a summarizer."
        user_part = "Content to summarize."
        result = call_llm_api(
            api_type="ollama",
            model="qwen2:latest",
            base_url_or_host="http://localhost:11434",
            system_part=system_part,
            user_part=user_part,
            timeout=120,
            max_retries=3,
        )

        assert result == "mock summary"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11434/api/generate"
        assert kwargs["json"] == {
            "model": "qwen2:latest",
            "prompt": system_part + user_part,
            "stream": False,
        }
        assert kwargs["timeout"] == 120


def test_call_llm_api_openrouter_success():
    """Test successful OpenRouter API call."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "mock summary"}}]
        }
        mock_post.return_value = mock_response

        system_part = "You are a summarizer."
        user_part = "Content to summarize."
        api_key = "test_api_key"
        result = call_llm_api(
            api_type="openrouter",
            model="google/gemma-2-9b-it",
            base_url_or_host="https://openrouter.ai/api/v1",
            system_part=system_part,
            user_part=user_part,
            api_key=api_key,
            timeout=120,
            max_retries=3,
        )

        assert result == "mock summary"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://openrouter.ai/api/v1/chat/completions"
        assert kwargs["headers"]["Authorization"] == f"Bearer {api_key}"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"] == {
            "model": "google/gemma-2-9b-it",
            "messages": [
                {"role": "system", "content": system_part},
                {"role": "user", "content": user_part},
            ],
            "stream": False,
        }
        assert kwargs["timeout"] == 120


def test_call_llm_api_openrouter_missing_key():
    """Test OpenRouter call with missing API key."""
    with pytest.raises(ValueError, match="OpenRouter API key is required"):
        call_llm_api(
            api_type="openrouter",
            model="google/gemma-2-9b-it",
            base_url_or_host="https://openrouter.ai/api/v1",
            system_part="system",
            user_part="user",
            api_key=None,
        )


def test_call_llm_api_unsupported_type():
    """Test unsupported API type."""
    with pytest.raises(ValueError, match="Unsupported API type"):
        call_llm_api(
            api_type="invalid",
            model="model",
            base_url_or_host="base",
            system_part="system",
            user_part="user",
        )


def test_call_llm_api_ollama_request_exception():
    """Test Ollama API call with request exception."""
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException(
            "Connection error"
        )

        with pytest.raises(ValueError, match="Ollama API call failed"):
            call_llm_api(
                api_type="ollama",
                model="qwen2:latest",
                base_url_or_host="http://localhost:11434",
                system_part="system",
                user_part="user",
            )


def test_call_llm_api_openrouter_rate_limit_retry():
    """Test OpenRouter rate limit handling with retry."""
    with patch("requests.post") as mock_post:
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "mock summary"}}]
        }

        mock_response_rate_limit = MagicMock()
        mock_response_rate_limit.status_code = 429
        mock_response_rate_limit.raise_for_status.side_effect = (
            requests.exceptions.HTTPError()
        )

        mock_post.side_effect = [
            mock_response_rate_limit,
            mock_response_success,
        ]

        system_part = "You are a summarizer."
        user_part = "Content to summarize."
        api_key = "test_api_key"
        result = call_llm_api(
            api_type="openrouter",
            model="google/gemma-2-9b-it",
            base_url_or_host="https://openrouter.ai/api/v1",
            system_part=system_part,
            user_part=user_part,
            api_key=api_key,
            timeout=120,
            max_retries=1,  # One retry
        )

        assert result == "mock summary"
        assert mock_post.call_count == 2  # Initial + one retry