
"""
Gemini language model integration used by Version 1 and Version 2.

This module centralizes communication with Google's Gemini API using
the google-genai Python library.

It includes support for configurable models, backup model selection,
and retry handling for temporary API errors such as quota restrictions
(429) and service availability problems (503).

The environment configuration is always retrieved from the project's
main directory, allowing the application to run from different locations
without affecting access to the API credentials.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv


# Resolve the application directory and locate its environment configuration.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


# Model preferences used when no custom configuration is provided.
DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_FALLBACKS = "gemini-2.5-flash-lite,gemini-2.5-flash"


def load_env():
    """Import the project's environment variables and prioritize .env values."""

    load_dotenv(ENV_PATH, override=True)


def key_problem():
    """Return a diagnostic message describing a possible API key issue."""

    if not ENV_PATH.exists():

        # Check whether the environment file was saved under another name.
        possible_files = (
            ".env.txt",
            ".env.rtf",
            "env",
            ".env.example.txt",
        )

        for filename in possible_files:
            if (PROJECT_ROOT / filename).exists():
                return (
                    f"I found '{filename}' in {PROJECT_ROOT} but not '.env'. "
                    "Rename it to exactly '.env' (no extension)."
                )

        return (
            f"There is no .env file in {PROJECT_ROOT}. "
            "Copy .env.example to .env and put your key in it."
        )

    # Inspect the file contents to determine why authentication may fail.
    file_content = ENV_PATH.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    if "GEMINI_API_KEY" not in file_content:
        return (
            f"{ENV_PATH} exists but has no line starting with "
            "GEMINI_API_KEY=."
        )

    if "your_gemini_api_key_here" in file_content:
        return (
            f"{ENV_PATH} still has the placeholder. "
            "Replace your_gemini_api_key_here with your real key and save."
        )

    return (
        f"{ENV_PATH} has a GEMINI_API_KEY line, but it's empty. "
        "Check the file is saved and restart the app."
    )


class LLMError(Exception):
    """Represents an error encountered while communicating with Gemini."""


class GeminiLLM:
    """Provides a reusable interface for Gemini text generation."""

    def __init__(self, api_key=None, model=None, fallbacks=None):

        # Reload settings so changes to the environment file are recognized.
        load_env()

        configured_key = api_key or os.getenv("GEMINI_API_KEY", "")

        self.api_key = (
            configured_key.strip()
            .strip('"')
            .strip("'")
        )

        # Determine which model should receive requests first.
        primary_model = (
            model
            or os.getenv("GEMINI_MODEL", "").strip()
            or DEFAULT_MODEL
        )

        # Obtain the alternative models from the supplied settings.
        fallback_models = (
            fallbacks
            or os.getenv("GEMINI_FALLBACK_MODELS", DEFAULT_FALLBACKS)
        )

        # Maintain the preferred order while avoiding duplicate model names.
        self.models = [primary_model] + [
            entry.strip()
            for entry in fallback_models.split(",")
            if entry.strip() and entry.strip() != primary_model
        ]

        # Delay SDK client creation until an API request is made.
        self._client = None

    @property
    def available(self):
        """Indicate whether a non-placeholder Gemini key is configured."""

        return bool(self.api_key) and "your_" not in self.api_key

    def _get_client(self):
        """Return the existing SDK client or initialize it when necessary."""

        if self._client is None:
            from google import genai

            self._client = genai.Client(
                api_key=self.api_key
            )

        return self._client

    def generate(self, system, contents, json_mode=False, retries=2):
        """
        Generate a response using the configured Gemini models.

        Parameters:
            system: System-level instructions for the model.
            contents: Input text or a sequence of conversation messages.
            json_mode: Requests a JSON-formatted response when enabled.
            retries: Maximum number of additional attempts for temporary errors.

        Returns:
            The generated response as a string.

        Raises:
            LLMError: If authentication or response generation fails.
        """

        if not self.available:
            raise LLMError(
                "No Gemini API key set. Add GEMINI_API_KEY to your .env file."
            )

        from google.genai import types

        # Apply generation settings based on the expected output format.
        generation_config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2 if json_mode else 0.8,
            response_mime_type=(
                "application/json" if json_mode else None
            ),
        )

        last_error = None

        # Process the available models according to their priority.
        for selected_model in self.models:

            for attempt_number in range(retries + 1):

                try:
                    response = self._get_client().models.generate_content(
                        model=selected_model,
                        contents=contents,
                        config=generation_config
                    )

                    return response.text or ""

                except Exception as error:

                    last_error = error
                    error_message = str(error)

                    # Identify errors that may disappear after waiting.
                    temporary_errors = (
                        "503",
                        "UNAVAILABLE",
                        "429",
                        "RESOURCE_EXHAUSTED",
                    )

                    if any(
                        error_code in error_message
                        for error_code in temporary_errors
                    ):
                        wait_time = 1.5 * (attempt_number + 1)
                        time.sleep(wait_time)
                        continue

                    # An unavailable model should not prevent trying alternatives.
                    if any(
                        error_code in error_message
                        for error_code in ("404", "NOT_FOUND")
                    ):
                        break

                    # Stop processing when an unrecoverable error occurs.
                    raise LLMError(
                        friendly_error(error_message)
                    ) from error

        # No model produced a response, so report the final encountered error.
        raise LLMError(
            friendly_error(str(last_error))
        )


def friendly_error(message):
    """Convert technical Gemini API errors into user-readable explanations."""

    if (
        "API key not valid" in message
        or "401" in message
        or "403" in message
    ):
        return (
            "The Gemini API key is not valid. "
            "Create a new one in Google AI Studio and put it in .env."
        )

    if "429" in message or "RESOURCE_EXHAUSTED" in message:
        return (
            "The free Gemini quota is used up for now. "
            "Wait a bit or try another model."
        )

    if "503" in message or "UNAVAILABLE" in message:
        return (
            "Gemini is overloaded right now. "
            "Wait a minute and try again."
        )

    if "404" in message or "NOT_FOUND" in message:
        return (
            "The Gemini model in .env wasn't found. "
            "Remove GEMINI_MODEL to use the default."
        )

    return f"Gemini error: {message[:200]}"
