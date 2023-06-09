"""
Utility constants and functions.
"""

# =============================================================================

import enum as _enum

# =============================================================================

__all__ = (
    "Color",
    "PieceType",
    "PromoteType",
    "EndGameState",
    "check_brc",
    "check_brc_bool",
)

# =============================================================================


class _EnumWIthTitle(_enum.Enum):
    """An enum class that adds a `title()` method."""

    def title(self) -> str:
        """Returns the enum name as a title string."""
        return self.name.title()


class Color(_EnumWIthTitle):
    """The colors for each piece."""

    WHITE = 0
    BLACK = 1

    def abbr(self) -> str:
        """Returns the first letter of the color."""
        return self.name[0]

    def other(self) -> "Color":
        """Returns the other color."""
        return Color(1 - self.value)


class PieceType(_EnumWIthTitle):
    """The piece types."""

    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    KNIGHT = "N"
    BISHOP = "B"
    PAWN = "P"


class PromoteType(_enum.Enum):
    """The piece types that can be promoted to."""

    QUEEN = PieceType.QUEEN
    ROOK = PieceType.ROOK
    KNIGHT = PieceType.KNIGHT
    BISHOP = PieceType.BISHOP

    @classmethod
    def by_index(cls, i: int) -> "PromoteType":
        """Returns the PromoteType at index i."""
        for j, p_type in enumerate(cls):
            if j == i:
                return p_type
        raise IndexError(f"invalid index {i} for {cls.__name__}")


class EndGameState(_enum.Enum):
    """The possible states for the end of the game."""

    CHECKMATE = _enum.auto()
    STALEMATE = _enum.auto()
    INSUFFICIENT_MATERIAL_DRAW = _enum.auto()
    FIFTY_MOVE_DRAW = _enum.auto()
    THREEFOLD_REPETITION_DRAW = _enum.auto()

    def human_readable(self) -> str:
        """Returns a human-readable name of this state."""
        return self.name.replace("_", " ").title()

    def is_draw(self) -> bool:
        """Returns whether the current state is a type of draw."""
        return self in (
            self.INSUFFICIENT_MATERIAL_DRAW,
            self.FIFTY_MOVE_DRAW,
            self.THREEFOLD_REPETITION_DRAW,
        )


# =============================================================================


def check_brc(bn=None, r=None, c=None, tr=None, tc=None):
    """Checks that all the given args are within the proper bounds.

    Raises `ValueError` if any conditions are not satisfied.
    """
    if bn is not None and bn not in (0, 1):
        raise ValueError("`bn` must be 0 or 1")
    for name, val in (("r", r), ("c", c), ("tr", tr), ("tc", tc)):
        if val is None:
            continue
        if not 0 <= val < 8:
            raise ValueError(f"`{name}` must be bounded within [0, 7]")


def check_brc_bool(bn=None, r=None, c=None, tr=None, tc=None) -> bool:
    """Returns True if all the given args are within the proper bounds."""
    try:
        check_brc(bn, r, c, tr, tc)
        return True
    except ValueError:
        return False
