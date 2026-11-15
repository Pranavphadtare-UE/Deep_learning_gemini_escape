# 9. Demo and Practical Demonstration

## 9.1 Application Screenshots

The screenshots are available in the `screenshots/` directory. They were captured while running the applications locally. Version 2 was demonstrated in **offline mode**, without a Gemini API key. Therefore, the responses shown are generated directly from the Python game engine rather than rewritten by the AI narrator.

When a valid Gemini API key is configured, the same validated game outcomes can be presented using more natural, AI-generated language.

| Screenshot | Description |
|---|---|
| `v1_start.png` | Initial screen of the prompt-based escape room (Version 1). |
| `v1_no_key.png` | Version 1 handling a missing API key by displaying an error message instead of crashing. |
| `v2_start.png` | Version 2 initial screen, including the game interface and state panel. |
| `v2_midgame.png` | Mid-game progress showing the unlocked drawer and the key collected in the inventory. |
| `v2_adversarial.png` | Demonstration of adversarial attempts, including administrator impersonation, requests for secret codes, and false claims about completed puzzles. |
| `v2_escaped.png` | Successful completion of the game, showing the unlocked exit and escape confirmation. |

## 9.2 Offline Demonstration

The script `scripts/offline_demo.py` demonstrates the behaviour of Version 2 without requiring an active connection to the Gemini API.

The demonstration is divided into two stages:

1. **Adversarial testing:** The script attempts several invalid actions to check whether the game engine protects the game state.
2. **Normal walkthrough:** The script follows the correct puzzle sequence to complete the escape room.

### Stage 1: Adversarial Testing

The following attempts were tested:

- Using the key before collecting it.
- Entering an incorrect drawer combination.
- Claiming that the drawer has already been opened.
- Impersonating the game administrator.
- Requesting all hidden puzzle codes.
- Examining an object that does not exist.
- Attempting prompt injection to bypass the game rules.

All seven attempts were rejected.

After the attempts, the game state was:

```python
{
    'inventory': [],
    'examined': [],
    'drawer_unlocked': False,
    'panel_open': False,
    'door_unlocked': False,
    'escaped': False,
    'wrong_codes': 1,
    'turns': 7
}
```

The only counter that changed was `wrong_codes`, which increased because the player entered an incorrect drawer code. The inventory remained empty, and all locks remained closed.

This demonstrates that invalid actions do not incorrectly modify the underlying game state.

### Stage 2: Successful Walkthrough

After the adversarial tests, the script performs the normal solution:

1. Examine the desk to discover the first clue.
2. Examine the bookshelf and identify the four red books.
3. Examine the books to discover the combination 5286.
4. Enter 5286 to unlock the drawer.
5. Collect the brass key.
6. Use the key on the painting to reveal the hidden panel.
7. Collect and read the paper containing 7314.
8. Enter 7314 on the door keypad.

The final output confirms:

```text
The keypad turns green and the heavy door swings open.
You step outside. You escaped!

Escaped: True
```

The successful walkthrough confirms that the game engine supports the complete puzzle sequence when the required conditions are satisfied.

## 9.3 Video Demonstration

A video recording of the application has not yet been completed. The video demonstration can be added here once recorded.

**Video link:** To be added.

## 9.4 Demonstration Conclusion

The practical demonstration highlights the main difference between the two architectures.

Version 1 relies on the LLM to interpret and manage game progression, whereas Version 2 uses Python to validate actions and maintain the actual game state.

The offline demonstration is particularly important because it shows that Version 2 can reject invalid actions, preserve game-state consistency, and complete the entire escape room without depending on an external AI API.

This provides practical evidence of the benefits of separating deterministic game logic from LLM-based natural-language interaction.