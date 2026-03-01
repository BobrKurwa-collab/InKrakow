"""
Game engine for InKrakow adventure game.
Handles game logic, collision detection, and state management.
"""

from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class Position:
    """Represents x, y coordinates in the game world."""
    x: int
    y: int

    def __add__(self, other: "Position") -> "Position":
        return Position(self.x + other.x, self.y + other.y)

    def __eq__(self, other):
        return isinstance(other, Position) and self.x == other.x and self.y == other.y


class Scene:
    """Represents a game scene with walls and interactive objects."""

    def __init__(self, width: int, height: int, walls: List[List[bool]], 
                 display_map: List[str]):
        """
        Initialize a scene.
        
        Args:
            width: Scene width in cells
            height: Scene height in cells
            walls: 2D list where True means cell is blocked
            display_map: ASCII characters to render each cell
        """
        self.width = width
        self.height = height
        self.walls = walls
        self.display_map = display_map

    def is_walkable(self, pos: Position) -> bool:
        """Check if a position is walkable (not a wall and within bounds)."""
        if pos.x < 0 or pos.x >= self.width or pos.y < 0 or pos.y >= self.height:
            return False
        return not self.walls[pos.y][pos.x]

    def get_display_char(self, pos: Position) -> str:
        """Get the character to display at a position."""
        if 0 <= pos.y < len(self.display_map):
            row = self.display_map[pos.y]
            if 0 <= pos.x < len(row):
                return row[pos.x]
        return "?"



class NPC:
    """Base class for non-player characters."""
    char: str = "?"

    def __init__(self, pos: Position):
        self.pos = Position(pos.x, pos.y)

    def update(self, game: "Game"):
        """Update NPC behavior each turn. Override in subclasses."""
        pass

    def distance_to_player(self, game: "Game") -> int:
        return abs(self.pos.x - game.player_pos.x) + abs(self.pos.y - game.player_pos.y)


class Policeman(NPC):
    char = "P"

    def update(self, game: "Game"):
        import random
        # move only occasionally to appear slow
        if random.random() < 0.3:
            directions = [(0,-1),(0,1),(-1,0),(1,0)]
            random.shuffle(directions)
            for dx, dy in directions:
                new = Position(self.pos.x + dx, self.pos.y + dy)
                # policeman treats player and objective as walkable
                if game.scene.is_walkable(new):
                    self.pos = new
                    break
        # catch player
        if self.pos == game.player_pos:
            game.game_over = True
            game.status_message = "Вас задержала полиция за нарушение общественного порядка"


class Pigeon(NPC):
    char = "o"

    def update(self, game: "Game"):
        import random
        # 8-directional move, fly over walls
        dirs = [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1),(0,0)]
        dx, dy = random.choice(dirs)
        new = Position(self.pos.x + dx, self.pos.y + dy)
        # keep within bounds
        if 0 <= new.x < game.scene.width and 0 <= new.y < game.scene.height:
            self.pos = new
        # may shit on player if share cell
        if self.pos == game.player_pos:
            # once dirtied, status stays
            if not game.permanent_status:
                game.permanent_status = "Обосран птицами"


class Hobo(NPC):
    char = "H"

    def update(self, game: "Game"):
        import random
        # move slowly (sleep more often)
        if random.random() < 0.7:
            return  # mostly sleeping
        directions = [(0,-1),(0,1),(-1,0),(1,0)]
        random.shuffle(directions)
        for dx, dy in directions:
            new = Position(self.pos.x + dx, self.pos.y + dy)
            if game.scene.is_walkable(new):
                self.pos = new
                break


class Game:
    """Main game class managing game state and logic."""

    def __init__(self, scene: Scene, player_start: Position, 
                 objective_pos: Position, npcs: List[NPC] = None,
                 fog_radius: int = 8, fog_enabled: bool = True):
        """
        Initialize game.
        
        Args:
            scene: The current game scene
            player_start: Starting position for the player
            objective_pos: Position of the objective (clothes)
            npcs: optional list of NPC objects
        """
        self.scene = scene
        self.player_pos = Position(player_start.x, player_start.y)
        self.objective_pos = Position(objective_pos.x, objective_pos.y)
        self.game_over = False
        self.won = False
        self.npcs: List[NPC] = npcs if npcs else []
        self.status_message: str = ""
        # persistent statuses
        self.permanent_status: str = ""
        # internal flag to preserve a status message set by player actions
        self._preserve_next_status = False
        # Krakow fog settings
        self.fog_enabled = fog_enabled
        self.fog_radius = fog_radius

    def move_player(self, direction: Tuple[int, int]) -> bool:
        """
        Attempt to move the player.
        
        Args:
            direction: (dx, dy) tuple for movement direction
            
        Returns:
            True if move was successful, False otherwise
        """
        if self.game_over:
            return False

        new_pos = self.player_pos + Position(direction[0], direction[1])

        # check hobo proximity restriction (increased smell radius)
        for npc in self.npcs:
            if isinstance(npc, Hobo):
                # use Manhattan distance; block if within 3 cells
                if abs(npc.pos.x - new_pos.x) + abs(npc.pos.y - new_pos.y) <= 3:
                    self.status_message = "Вы видите бомжа, идти дальше невозможно, слезятся глаза"
                    # preserve this message so it's visible on the next render
                    self._preserve_next_status = True
                    return False

        if not self.scene.is_walkable(new_pos):
            return False

        # check policeman collision
        for npc in self.npcs:
            if isinstance(npc, Policeman) and npc.pos == new_pos:
                self.game_over = True
                self.status_message = "Вас задержала полиция за нарушение общественного порядка"
                self.player_pos = new_pos
                return True

        self.player_pos = new_pos

        # Check if player reached the objective
        if self.player_pos == self.objective_pos:
            self.game_over = True
            self.won = True

        return True

    def update_npcs(self):
        """Advance NPCs and handle interactions."""
        # clear only temporary status (permanent ones preserved)
        # if a status was just set by a player action, preserve it for one render
        if getattr(self, '_preserve_next_status', False):
            self._preserve_next_status = False
        else:
            self.status_message = ""

        for npc in list(self.npcs):
            npc.update(self)

        # policeman arrests hobo
        removals = []
        for npc in self.npcs:
            if isinstance(npc, Policeman):
                for other in self.npcs:
                    if isinstance(other, Hobo) and npc.pos == other.pos:
                        removals.append(npc)
                        removals.append(other)
                        self.status_message = "Полицейский арестовал бомжа"
        for r in removals:
            if r in self.npcs:
                self.npcs.remove(r)

        # check if policeman now on player after move
        for npc in self.npcs:
            if isinstance(npc, Policeman) and npc.pos == self.player_pos:
                self.game_over = True
                self.status_message = "Вас задержала полиция за нарушение общественного порядка"

    def get_game_state(self) -> dict:
        """Get current game state."""
        return {
            "player_pos": self.player_pos,
            "objective_pos": self.objective_pos,
            "game_over": self.game_over,
            "won": self.won,
            "npcs": self.npcs,
            "status_message": self.status_message,
            "permanent_status": self.permanent_status,
            "krakow_fog_enabled": self.fog_enabled,
            "krakow_fog_radius": self.fog_radius,
        }
