
"""
Web interface for Version 1 of the AI Escape Room, implemented with Gradio.

To launch the application directly, execute:

    python app_v1.py

You can also start this version through the project launcher:

    python run.py v1
"""

import gradio as gr

from escape_room.gemini_client import GeminiLLM
from escape_room.prompt_game_master import GameV1


WELCOME_MESSAGE = """
# AI Escape Room – Version 1

*Powered entirely by an LLM.*

You find yourself trapped inside an abandoned library.
Explore the surroundings, uncover hidden clues, solve the mystery,
and discover a way to unlock the exit.

**Note:** A valid Gemini API key is required to play this version.
"""


def initialize_game():
    """Set up a new game instance and prepare the initial conversation."""

    game_session = GameV1(GeminiLLM())

    conversation_history = [
        {
            "role": "assistant",
            "content": game_session.intro(),
        }
    ]

    return game_session, conversation_history


def process_player_input(message, chat_history, session):
    """Handle a submitted command and append the resulting messages to chat."""

    # Ignore empty submissions without modifying the current session.
    if not message.strip():
        return "", chat_history, session

    response = session.turn(message)

    # Add both the player's command and the Game Master's response.
    conversation_history = chat_history + [
        {
            "role": "user",
            "content": message,
        },
        {
            "role": "assistant",
            "content": response,
        },
    ]

    return "", conversation_history, session


def start_over(session):
    """Replace the existing game with a newly initialized session."""

    # A fresh initialization also reloads the environment configuration.
    return initialize_game()


def create_interface():
    """Configure the Gradio application and register its event callbacks."""

    with gr.Blocks(title="AI Escape Room - Version 1") as interface:

        gr.Markdown(WELCOME_MESSAGE)

        # Keep the game object available throughout the current session.
        game_state = gr.State()

        # Display the ongoing interaction between the player and Gemini.
        chat_window = gr.Chatbot(
            height=460,
            label="Game Master",
        )

        # Allow the player to enter commands describing their actions.
        command_box = gr.Textbox(
            placeholder="e.g. examine the bookshelf",
            label="What do you do?",
        )

        with gr.Row():
            send_button = gr.Button(
                "Send",
                variant="primary",
            )

            restart_button = gr.Button("Restart game")

        # Load a new game and its opening message when the app starts.
        interface.load(
            initialize_game,
            outputs=[game_state, chat_window],
        )

        # Process commands submitted using the Enter key.
        command_box.submit(
            process_player_input,
            inputs=[command_box, chat_window, game_state],
            outputs=[command_box, chat_window, game_state],
        )

        # Provide the same functionality through the Send button.
        send_button.click(
            process_player_input,
            inputs=[command_box, chat_window, game_state],
            outputs=[command_box, chat_window, game_state],
        )

        # Reset the conversation and create a fresh game session.
        restart_button.click(
            start_over,
            inputs=[game_state],
            outputs=[game_state, chat_window],
        )

    return interface


if __name__ == "__main__":
    application = create_interface()
    application.launch()
