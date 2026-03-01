"""
Visualization module for InKrakow game.
Handles ASCII rendering of game state to console.
"""

from game_engine import Game, Position, Scene


class ConsoleRenderer:
    """Renders game state to ASCII console."""

    PLAYER_CHAR = "@"
    OBJECTIVE_CHAR = "*"
    # Adjusted for ASCII character aspect ratio (~2:1 height:width)
    # Using narrower viewport width to compensate and make view more square
    VIEWPORT_WIDTH = 71
    VIEWPORT_HEIGHT = 31

    @staticmethod
    def render(game: Game) -> str:
        """
        Render the current game state as ASCII with player-centered viewport.
        Player stays in center; scene scrolls around them.
        
        Args:
            game: Game object to render
            
        Returns:
            String containing the rendered game state (viewport around player)
        """
        output = []
        scene = game.scene
        player = game.player_pos
        
        # Calculate viewport bounds with player centered
        half_w = ConsoleRenderer.VIEWPORT_WIDTH // 2
        half_h = ConsoleRenderer.VIEWPORT_HEIGHT // 2
        
        cam_x = player.x - half_w
        cam_y = player.y - half_h
        
        fog_enabled = getattr(game, 'krakow_fog_enabled', True)
        fog_radius = getattr(game, 'krakow_fog_radius', 8)
        
        # Render viewport
        for vy in range(ConsoleRenderer.VIEWPORT_HEIGHT):
            row = []
            for vx in range(ConsoleRenderer.VIEWPORT_WIDTH):
                # World position
                world_x = cam_x + vx
                world_y = cam_y + vy
                
                # Check bounds
                if world_x < 0 or world_x >= scene.width or world_y < 0 or world_y >= scene.height:
                    row.append(' ')
                    continue
                
                pos = Position(world_x, world_y)
                
                # Krakow fog handling using Euclidean distance from player
                visible = True
                if fog_enabled:
                    dx = world_x - player.x
                    dy = world_y - player.y
                    if (dx*dx + dy*dy) > (fog_radius * fog_radius):
                        visible = False
                
                if not visible:
                    row.append('.')
                    continue
                
                # Check if player is at this position
                if pos == game.player_pos:
                    row.append(ConsoleRenderer.PLAYER_CHAR)
                # Check if objective is at this position
                elif pos == game.objective_pos:
                    row.append(ConsoleRenderer.OBJECTIVE_CHAR)
                else:
                    # check NPCs
                    npc_here = None
                    for npc in getattr(game, 'npcs', []):
                        if npc.pos == pos:
                            npc_here = npc
                            break
                    if npc_here:
                        row.append(npc_here.char)
                    else:
                        # Otherwise render scene character
                        row.append(scene.get_display_char(pos))
            
            output.append("".join(row))
        
        return "\n".join(output)

    @staticmethod
    def render_with_info(game: Game) -> str:
        """Render game state with additional info."""
        game_view = ConsoleRenderer.render(game)
        info = f"\nPlayer: ({game.player_pos.x}, {game.player_pos.y}) | "
        info += f"Objective: ({game.objective_pos.x}, {game.objective_pos.y})"
        if game.status_message:
            info += f" | {game.status_message}"
        if hasattr(game, 'permanent_status') and game.permanent_status:
            info += f" | {game.permanent_status}"
        
        if game.game_over:
            if game.won:
                info += " | YOU FOUND YOUR CLOTHES! YOU WIN!"
            else:
                info += " | GAME OVER"
        
        return game_view + info
