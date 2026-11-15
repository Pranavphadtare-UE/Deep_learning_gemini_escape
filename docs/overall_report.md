# AI Escape Room – Project Report

**Name:** [Your Name]  
**Course:** MSc Computer Science, University of Europe for Applied Sciences  
**Project:** Mini Project – AI-Powered Escape Room

## 1. What I built

I developed a text-based AI Escape Room game in which a player is trapped inside a locked room and must solve a sequence of puzzles to escape. Google Gemini acts as the AI component, allowing players to interact with objects and solve puzzles using natural language.

I implemented the game in two different versions to compare two approaches to building LLM-powered applications:

- **Version 1 – Prompt-Based:** The LLM acts as the Game Master and manages the game through prompts and conversation history.
- **Version 2 – State-Based:** Python manages the game rules and state, while the LLM is primarily responsible for understanding natural language and generating responses.

Both versions use the same escape room scenario, allowing a comparison of their reliability, flexibility, and resistance to invalid player actions.

## 2. The Room and the Puzzles

The game takes place in a locked room containing five interactive objects:

1. **Desk:** Contains a carving that provides the first clue: "The books know the way to the drawer."
2. **Bookshelf:** Contains four red books with numbers that reveal the first combination: **5286**.
3. **Locked Drawer:** The combination 5286 unlocks the drawer, allowing the player to collect a small brass key.
4. **Painting:** Contains a hidden keyhole. Using the brass key reveals a concealed panel containing a paper with the second combination: **7314**.
5. **Door with Keypad:** The player enters 7314 to unlock the door and escape.

The puzzles follow a sequential structure. Each successful action provides information or an item needed for the next stage.

The objective was to create a short but interactive experience in which the player must examine objects, discover clues, collect items, and solve puzzles in the correct order.

## 3. Version 1 – Prompt-Based Architecture

In Version 1, the LLM acts as the complete Game Master. The application uses a system prompt containing the room description, interactive objects, puzzle sequence, solutions, and game rules.

The player interacts with the game through the Gradio interface. Each message is added to the conversation history, and the game manager sends the conversation context to Gemini to generate the next response.

The main components are:

- **`app_prompt_based.py`:** Provides the Gradio interface for player interaction.
- **`escape_room/prompt_game_master.py`:** Implements the Version 1 game manager and handles conversation history.
- **`escape_room/gemini_client.py`:** Handles communication with the Gemini API.
- **System Prompt:** Defines the room, puzzles, solutions, and rules that guide the LLM.

### How it works

1. The player enters a natural-language action, such as "examine the bookshelf".
2. The application passes the message to the game manager.
3. The game manager adds the message to the conversation history.
4. The system prompt and conversation history are sent to Gemini.
5. Gemini interprets the action and generates a response.
6. The response is displayed in the Gradio interface.
7. The conversation continues until the game reaches its completion condition.

### Problems with Version 1

Although this approach is easy to implement and produces natural conversations, it has several limitations:

- **No independent game state:** The game relies on conversation history to remember whether an object has been examined or a puzzle has been solved.
- **LLM controls game progression:** The model decides whether a player's requested action is successful.
- **Prompt injection vulnerability:** A player may attempt to manipulate the model by claiming to be an administrator or instructing it to ignore previous rules.
- **Secret information exposure:** Puzzle solutions are included in the system prompt, which means the model has access to them throughout the game.
- **Inconsistent responses:** The model may occasionally forget previous events, invent objects, or contradict earlier responses.
- **Growing conversation history:** Sending the complete conversation repeatedly can increase token usage and response time.

These limitations demonstrate why relying entirely on an LLM for application logic can be problematic.

## 4. Version 2 – State-Based Architecture

For Version 2, I redesigned the application by separating game logic from natural-language processing.

The main principle is that **Python controls the game, while the LLM handles language**.

Instead of allowing Gemini to decide whether an action succeeds, the application converts player messages into structured actions and passes them to a Python game engine. The engine validates each action against the actual game state before making any changes.

### Main components

- **`app_state_based.py`:** Provides the Gradio interface for the state-based game.
- **`escape_room/v2/game_controller.py`:** Coordinates the complete game workflow.
- **`escape_room/v2/intent_parser.py`:** Converts natural-language messages into structured player intents.
- **`escape_room/v2/game_engine.py`:** Contains the game rules and validates player actions.
- **`escape_room/v2/game_state.py`:** Maintains the current game state, including inventory, examined objects, puzzle progress, and escape status.
- **`escape_room/v2/game_config.py`:** Contains the game configuration and puzzle-related information.
- **`escape_room/v2/game_narrator.py`:** Generates player-friendly responses based on validated game outcomes.
- **`escape_room/gemini_client.py`:** Handles communication with the Gemini API.

### How one turn works

1. The player enters an action, such as "take the key from the drawer".
2. The Gradio interface sends the message to the game controller.
3. The intent parser identifies the requested action and extracts relevant information.
4. The game engine receives the structured intent and checks the current game state.
5. The engine validates requirements such as inventory, puzzle completion, object accessibility, and correct codes.
6. If the action is valid, Python updates the game state. If it is invalid, the state remains unchanged.
7. The narrator converts the validated result into a natural-language response.
8. The response is displayed to the player through the Gradio interface.

### Why Version 2 is more reliable

- **Structured game state:** Game progress is maintained using Python data structures rather than relying entirely on conversation history.
- **Deterministic validation:** The engine decides whether an action is valid using predefined rules.
- **Better protection against manipulation:** A player cannot unlock an object simply by claiming that it has already been unlocked.
- **Separation of responsibilities:** Parsing, game logic, state management, and narration are handled by separate components.
- **Controlled state changes:** Invalid actions do not modify the actual game state.
- **Offline support:** The application can use fallback mechanisms for supported actions and plain-text narration when Gemini is unavailable.

This architecture makes the game more predictable, easier to test, and less dependent on the behaviour of the LLM.

## 5. Testing and Evaluation

Testing was an important part of the development process, particularly for Version 2, where the game engine must enforce the rules correctly.

I implemented automated tests using **pytest** to check the parser, game engine, narrator, and game controller.

The project contains 61 automated tests, all of which passed successfully.

### Test results

| Test module | Number of tests | Result |
|---|---:|---|
| `tests/test_engine.py` | 26 | Passed |
| `tests/test_narrator_and_game.py` | 11 | Passed |
| `tests/test_parser.py` | 24 | Passed |
| **Total** | **61** | **All passed** |

### Important scenarios tested

The testing process covered scenarios such as:

- Attempting to collect an item before unlocking its location.
- Entering incorrect puzzle combinations.
- Attempting to use an item that is not in the inventory.
- Claiming that a puzzle has already been solved.
- Attempting administrative overrides or rule manipulation.
- Requesting hidden puzzle solutions.
- Interacting with nonexistent objects.
- Attempting to bypass the intended puzzle sequence.
- Checking that invalid actions do not change the game state.
- Completing the full escape room successfully.

I also created `scripts/offline_demo.py` to demonstrate invalid player actions and a complete successful walkthrough without depending on the Gemini API.

The offline demonstration confirmed that invalid actions were rejected and that the game could be completed by following the correct puzzle sequence.

## 6. Challenges Faced During Development

Several technical challenges arose during the implementation.

- **Gemini API integration:** Configuring the Gemini API and handling model availability and API errors required additional debugging.
- **Library compatibility:** The application required compatible versions of the Gemini SDK and Gradio.
- **Module renaming:** During project restructuring, several Python modules were renamed. This caused outdated import references that had to be corrected in the application and internal modules.
- **Natural-language parsing:** Converting different player expressions into consistent structured actions was challenging. The parser needed to identify the intended action, target, item, and code.
- **Game-state consistency:** Ensuring that invalid actions never modify the game state required separating action validation from state updates.
- **Narrative generation:** The narrator needed to produce natural responses without contradicting the facts returned by the game engine.
- **Offline testing:** I needed the game logic and automated tests to work without requiring an active Gemini API connection.

These challenges helped improve the modularity and reliability of the final application.

## 7. Limitations

Despite the improvements in Version 2, some limitations remain:

- **Natural-language ambiguity:** The parser may not understand unusual or complicated player instructions. In such cases, the player may need to rephrase the action.
- **LLM dependency:** When Gemini is used for narrative generation, response quality and availability depend on the external API.
- **Configuration security:** Puzzle information stored in local project files could be inspected by someone with access to the source code. A production application should keep sensitive game configuration on a protected server.
- **In-memory state:** The current game state is not permanently stored. Restarting the application may reset the player's progress.
- **Limited game environment:** The current implementation focuses on one room with a predefined sequence of puzzles. Supporting multiple rooms and dynamic puzzle generation would require further development.

## 8. What I Learned

The biggest lesson from this project was understanding the difference between using an LLM to generate responses and using an LLM to control an application.

Version 1 demonstrated how quickly an interactive application can be developed using prompts and conversation history. However, it also showed that natural-language instructions alone cannot guarantee consistent application behaviour.

Version 2 demonstrated the importance of deterministic application logic. By moving game-state management and action validation into Python, I reduced the risks associated with inconsistent model responses and prompt manipulation.

I also gained practical experience with Python application architecture, Gemini API integration, Gradio interfaces, natural-language parsing, state management, modular programming, and automated testing.

**Overall, this project demonstrated that LLMs are most effective when used alongside reliable application logic rather than being given complete control over it.**