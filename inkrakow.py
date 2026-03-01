"""
Main game loop for InKrakow adventure game.
Handles user input and game flow.
"""

import json
import sys
import os
from pathlib import Path

# Handle different OS key input methods
if sys.platform == "win32":
    import msvcrt
else:
    import select

from game_engine import Game, Scene, Position
from visualization import ConsoleRenderer


def load_scene_from_json(json_path: str) -> Scene:
    """Load a scene from a JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Convert wall_map strings to 2D boolean list
    walls = []
    for row_str in data["wall_map"]:
        walls.append([c == '1' for c in row_str])

    return Scene(
        width=data["width"],
        height=data["height"],
        walls=walls,
        display_map=data["display_map"]
    )


def get_direction_input() -> tuple or None:
    """
    Get directional input from the user. Only WASD keys are used for movement.

    Returns a (dx, dy) tuple or None if no valid movement key was pressed.
    """
    # Only WASD keys are used for movement; other input is ignored.
    if sys.platform == "win32":
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # Normalize ASCII letters to lowercase for WASD.
            if key.lower() in (b'w', b'a', b's', b'd'):
                mapping = {b'w': (0, -1), b's': (0, 1), b'a': (-1, 0), b'd': (1, 0)}
                return mapping[key.lower()]
    else:
        # Unix/macOS: use select with 0 timeout for non-blocking read
        try:
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                key = sys.stdin.read(1)
                if key.lower() == 'w':
                    return (0, -1)
                elif key.lower() == 's':
                    return (0, 1)
                elif key.lower() == 'a':
                    return (-1, 0)
                elif key.lower() == 'd':
                    return (1, 0)
        except Exception:
            pass
    return None


def main():
    """Main game loop."""
    # Find scenes directory
    current_dir = Path(__file__).parent
    scene_path = current_dir / "scenes" / "market_square.json"

    if not scene_path.exists():
        print(f"Error: Scene file not found at {scene_path}")
        sys.exit(1)

    # Load scene
    scene = load_scene_from_json(str(scene_path))

    # Load game data from JSON
    with open(scene_path, 'r') as f:
        scene_data = json.load(f)

    player_start = Position(
        scene_data["player_start"]["x"],
        scene_data["player_start"]["y"]
    )
    objective_pos = Position(
        scene_data["objective"]["x"],
        scene_data["objective"]["y"]
    )

    # create NPC objects if defined
    npcs = []
    if "npcs" in scene_data:
        from game_engine import Policeman, Pigeon, Hobo
        for entry in scene_data["npcs"]:
            t = entry.get("type")
            pos = Position(entry.get("x", 0), entry.get("y", 0))
            if t == "policeman":
                npcs.append(Policeman(pos))
            elif t == "pigeon":
                npcs.append(Pigeon(pos))
            elif t == "hobo":
                npcs.append(Hobo(pos))

    # Initialize game
    game = Game(scene, player_start, objective_pos, npcs)

    print("=" * 60)
    print("INKRAKOW - Drunken Adventures in Krakow")
    print("=" * 60)
    print("Controls: Use WASD keys to move")
    print("Objective: Find your clothes (marked with *)")
    print("=" * 60)
    print()

    # Main game loop
    running = True
    while running:
        # Clear screen
        os.system('cls' if sys.platform == "win32" else 'clear')

        # Get input (non-blocking)
        direction = get_direction_input()
        if direction:
            game.move_player(direction)

        # Update NPCs after player's action so status messages from movement remain visible
        game.update_npcs()

        # Render current state
        print(ConsoleRenderer.render_with_info(game))

        if game.game_over:
            if game.won:
                print("\nВы собрали все свои вещи и успешно покинули Краков! Поздравляем, вы выиграли!")
            running = False
            break

        # Small delay to avoid CPU spinning
        import time
        time.sleep(0.05)


if __name__ == "__main__":
    main()
