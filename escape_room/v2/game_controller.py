
"""
Main controller for Version 2 of the AI Escape Room.

Each player interaction follows three stages:
    1. Parse the player's input into a structured action.
    2. Execute the action through the Python game engine.
    3. Generate a natural language response describing the outcome.

This module connects the parser, game engine, and narration components.

The game can operate without Gemini. In offline mode, player commands
are interpreted using the regex-based parser and responses are generated
by the built-in narration system.
"""

from .game_config import load_config, secret_codes
from .game_engine import apply
from .intent_parser import parse_with_llm, parse_with_regex
from .game_narrator import narrate_plain, narrate_with_llm
from .game_state import new_state


class GameV2:
    """Coordinates gameplay, action processing, and response generation."""

    def __init__(self, llm=None, config=None):
        # An unavailable LLM allows the game to run in offline mode.
        self.llm = llm

        # Use the supplied room configuration or load the default one.
        self.config = config or load_config()

        # Keep puzzle solutions available for internal narration controls.
        self.secrets = secret_codes(self.config)

        # Initialize the game with a fresh state.
        self.state = new_state()

    @property
    def online(self):
        """Check whether the Gemini integration is ready for use."""

        return self.llm is not None and self.llm.available

    def intro(self):
        """Prepare the opening description and example player commands."""

        instructions = (
            "\n\nType things like *examine the desk*, "
            "*take the key* or *enter 1234 on the door*."
        )

        return self.config["intro"] + instructions

    def restart(self):
        """Clear the current progress and initialize a new game state."""

        self.state = new_state()

    def turn(self, text, intent=None):
        """
        Process a single player interaction.

        If an intent is provided directly, it is used without invoking
        the parser. Otherwise, the appropriate parser is selected
        according to the current online or offline mode.

        Returns:
            tuple: Generated response, parsed intent, and engine result.
        """

        # Convert natural language into a structured game action.
        if intent is None:

            if self.online:
                intent = parse_with_llm(self.llm, text)
            else:
                intent = parse_with_regex(text)

        # Let the Python engine validate and execute the requested action.
        result = apply(
            self.state,
            self.config,
            intent
        )

        # Generate the response using the active narration method.
        if self.online:
            response = narrate_with_llm(
                self.llm,
                text,
                result,
                self.secrets
            )
        else:
            response = narrate_plain(result)

        return response, intent, result
