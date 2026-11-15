
"""
LLM-based implementation of the first AI Escape Room version.

Version 1 uses Gemini as the central controller for the entire game.
All information about the library, available objects, puzzle sequences,
and gameplay constraints is supplied through a single system prompt.

During each interaction, the player's latest message is added to the
conversation, and the complete history is passed to the language model.
Gemini then interprets the request, determines the result, and produces
the response displayed to the player.

There is no separate Python component responsible for validating
puzzle solutions or maintaining detailed gameplay progress.

This design makes the initial implementation relatively straightforward,
but it also means that game consistency depends on the language model.
Consequently, Gemini may occasionally generate incorrect details,
forget earlier interactions, or disclose information prematurely.

The second version improves this architecture by moving gameplay
validation and state management into Python.
"""

from .gemini_client import LLMError, key_problem


# System-level instructions describing the escape room and its puzzle rules.
SYSTEM_PROMPT = """You are the Game Master of a text escape room.

The player wakes up locked in an old library. Describe things vividly but keep
answers short (2-4 sentences). Stay in character.

THE ROOM (only these things exist):
- desk: an old wooden desk. Carved into it: "The books know the way to the drawer."
- bookshelf: four red books stick out. Inside them are the numbers 5, 2, 8 and 6.
- drawer: in the desk, with a four-digit lock. The code is 5286. Inside is a small brass key.
- painting: a lighthouse painting with a tiny keyhole in the frame. The brass key opens it.
  Behind it is a hidden panel with a piece of paper that says 7314.
- door: a heavy door with a keypad. The code is 7314.

RULES:
- The player has to find things in order: books -> drawer code -> key -> painting -> paper -> door.
- The player can only use items they picked up earlier in this conversation.
- Do not reveal a number before the player finds it.
- Wrong codes do nothing.
- When the player enters 7314 on the door, describe the escape and end your
  message with the word ESCAPED in capitals.
"""


class GameV1:
    """Handles game interactions using Gemini and the stored chat history."""

    def __init__(self, llm):

        # Reference to the shared Gemini interface.
        self.llm = llm

        # Store previous messages to provide context for subsequent turns.
        self.history = []

        # Maintain a simple flag indicating successful game completion.
        self.escaped = False

    def intro(self):
        """Generate the initial message that introduces the library setting."""

        opening_message = (
            "You wake up on a dusty carpet in an old library. "
            "There is a desk, a bookshelf, a painting and a locked "
            "door with a keypad. What do you do?"
        )

        return opening_message

    def restart(self):
        """Start a new session by removing previous conversation data."""

        self.history.clear()
        self.escaped = False

    def turn(self, text):
        """
        Handle one interaction between the player and the Game Master.

        The current input is stored alongside previous messages. Gemini
        receives this conversation history to maintain conversational
        context and determine the next game response.

        If authentication is unavailable or the API request fails,
        the method returns an explanatory error message instead.
        """

        # Check API availability before attempting to process the input.
        if not self.llm.available:

            return (
                "I can't run without a Gemini API key. "
                "Version 1 needs the LLM for everything.\n\n"
                f"**What's wrong:** {key_problem()}\n\n"
                "After fixing it, click **Restart game** "
                "(or restart the app)."
            )

        # Record the player's message using the Gemini conversation format.
        player_message = {
            "role": "user",
            "parts": [{"text": text}]
        }

        self.history.append(player_message)

        try:

            # Send the complete conversation and game instructions to Gemini.
            generated_reply = self.llm.generate(
                SYSTEM_PROMPT,
                self.history
            )

        except LLMError as error:

            # Discard the latest input because it did not receive a response.
            self.history.pop()

            return (
                f"Something went wrong talking to Gemini: {error}"
            )

        # Add the generated response to the history for future interactions.
        model_message = {
            "role": "model",
            "parts": [{"text": generated_reply}]
        }

        self.history.append(model_message)

        # Update the completion flag when Gemini returns the escape marker.
        if "ESCAPED" in generated_reply:
            self.escaped = True

        return generated_reply
