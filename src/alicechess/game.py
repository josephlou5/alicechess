"""
Game class.
"""

# =============================================================================

from typing import Type

from alicechess.game_state import GameState
from alicechess.player import AnyPlayer, _PlayerBase

# =============================================================================

__all__ = ("Game",)

# =============================================================================


class Game:
    """Represents a game of Alice Chess."""

    def __init__(self, *, white: Type[AnyPlayer], black: Type[AnyPlayer]):
        """Initializes a Game with the given players.

        The players must be subclasses of `Player` (not instances).

        Args:
            white (Type[Player]): The player for white.
            black (Type[Player]): The player for black.
        """

        if not isinstance(white, type):
            raise TypeError("`white` must be a class (not an instance)")
        if not isinstance(black, type):
            raise TypeError("`black` must be a class (not an instance)")
        if not issubclass(white, _PlayerBase):
            raise TypeError("`white` must be a Player subclass")
        if not issubclass(black, _PlayerBase):
            raise TypeError("`black` must be a Player subclass")

        self._white = white
        self._black = black

    def new(self) -> GameState:
        """Returns a new game."""
        return GameState.new(white=self._white, black=self._black)

    def start_window(self, **kwargs):
        """Starts the game in a window.

        Any keyword arguments will be passed to the `Window`
        constructor.
        """
        # import here so that games that don't use the window don't need
        # to be run in a virtual environment (requires Pillow)
        # pylint: disable=import-outside-toplevel
        from alicechess.window import Window

        game_state = self.new()
        window = Window(game_state, **kwargs)
        window.run()
