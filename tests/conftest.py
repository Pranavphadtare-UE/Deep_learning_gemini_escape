
import sys
from pathlib import Path

import pytest


# Include the project root so the application modules can be imported.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from escape_room.v2.game_config import load_config  # noqa: E402
from escape_room.v2.game_state import new_state  # noqa: E402


@pytest.fixture
def config():
    """Provide the default escape room configuration for each test."""
    return load_config()


@pytest.fixture
def state():
    """Create a clean game state before running a test."""
    return new_state()


class FakeLLM:
    """
    Lightweight substitute for Gemini used in automated tests.

    It allows the application to follow its online execution path without
    requiring an actual API key or an internet connection. Predefined
    responses can be supplied, and API failures can also be simulated.
    """

    available = True
    models = ["fake-model"]

    def __init__(self, replies=None, error=None):
        # Store the responses that should be returned in sequence.
        self.replies = list(replies or [])

        # Optional exception used to simulate a failed API request.
        self.error = error

        # Keep a record of every request received by the mock.
        self.calls = []

    def generate(self, system, contents, json_mode=False):
        """Record a request and return a prepared response or raise an error."""

        self.calls.append((system, contents, json_mode))

        if self.error:
            raise self.error

        if self.replies:
            return self.replies.pop(0)

        return ""


@pytest.fixture
def fake_llm():
    """Expose the mock language model class to the test suite."""
    return FakeLLM
