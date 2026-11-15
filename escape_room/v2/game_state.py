
"""
Maintains the current progress of the Version 2 Escape Room.

The game state is the authoritative record of the player's progress.
It stores collected items, inspected objects, puzzle progress, and
the actions performed during the game.

Chat history is maintained separately for displaying the conversation.
It does not determine whether a puzzle has been solved or an action
has been completed.

Whenever the displayed conversation and the actual game progress
conflict, the information stored in this state dictionary takes priority.
"""


def new_state():
    """
    Create and return a fresh game state.

    All puzzle-related flags are initialized to False, while the
    player's inventory, examined objects, and activity log start empty.
    """

    initial_state = {
        "inventory": [],          # Items successfully collected by the player
        "examined": [],            # Room objects that have been inspected
        "drawer_unlocked": False,  # Indicates whether the drawer is open
        "panel_open": False,       # Tracks the hidden compartment behind the painting
        "door_unlocked": False,    # Indicates whether the exit door is unlocked
        "escaped": False,          # Records whether the player has escaped
        "wrong_codes": 0,          # Number of incorrect keypad combinations
        "turns": 0,                # Total number of player interactions
        "log": [],                 # Record of actions and their outcomes
    }

    return initial_state


def summary(state):
    """
    Generate a readable overview of the current game progress.

    This information is intended for the status panel in the Gradio
    interface and reflects the values stored in the game state.
    """

    # Display the collected items or indicate an empty inventory.
    inventory_text = ", ".join(state["inventory"]) or "nothing"

    # Prepare the individual status entries.
    status_lines = [
        f"**Inventory:** {inventory_text}",
        f"**Drawer:** {'open' if state['drawer_unlocked'] else 'locked'}",
        f"**Painting panel:** {'open' if state['panel_open'] else 'closed'}",
        f"**Door:** {'unlocked' if state['door_unlocked'] else 'locked'}",
        (
            f"**Turns:** {state['turns']}  |  "
            f"**Wrong codes:** {state['wrong_codes']}"
        ),
    ]

    # Include a completion message after the player successfully escapes.
    if state["escaped"]:
        status_lines.append("**You escaped!**")

    return "\n\n".join(status_lines)
