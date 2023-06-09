"""
Player class.
"""

# =============================================================================

import typing as _t

import utils as _utils
from position import Move as _Move

# =============================================================================

__all__ = (
    "Player",
    "HumanPlayer",
)

# =============================================================================


class _PlayerBase:
    """Base class for a player.."""

    is_human = False

    def __init__(self, color: _utils.Color):
        """Initializes a player."""
        self._color = color

    @property
    def color(self) -> _utils.Color:
        """The player color."""
        return self._color


class Player(_PlayerBase):
    """Represents a player.

    Properties:
        color (Color): The player color.
        is_human (bool): Whether this player is human.

    Methods:
        make_move(game_state) -> Move
            Called when this player should make their next move.
        promote(game_state) -> PromoteType
            Called when this player can promote a pawn.
    """

    def make_move(self, game_state: "GameState") -> _Move:
        """Called when this player should make their next move.

        Args:
            game_state (GameState): The current game state.

        Returns:
            Move: The move to make.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}: method `make_move()` not implemented"
        )

    def promote(self, game_state: "GameState") -> _utils.PromoteType:
        """Called when this player can promote a pawn.

        The move being made is accessible through `game_state.move`.

        Args:
            game_state (GameState): The current game state.

        Returns:
            PromoteType: The piece type to promote to.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}: method `promote()` not implemented"
        )


class HumanPlayer(_PlayerBase):
    """Represents a human player."""

    is_human = True


# =============================================================================

AnyPlayer = _t.Union[Player, HumanPlayer]
