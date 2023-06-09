"""
Pawn piece.
"""

# =============================================================================

from alicechess.pieces.piece import Piece
from alicechess.utils import Color, PieceType

# =============================================================================


class Pawn(Piece):
    """Pawn piece.

    Properties:
        dr (int): The direction of movement.
        can_promote (bool): Whether the pawn can be promoted.
    """

    _type = PieceType.PAWN

    def __init__(self, *args, **kwargs):
        """Initializes a Pawn piece."""
        super().__init__(*args, **kwargs)

        if self._color is Color.WHITE:
            # going up
            self._dr = -1
            self._start_row = 6
            self._promote_row = 0
        else:
            # going down
            self._dr = 1
            self._start_row = 1
            self._promote_row = 7

    def _check_start_position(self) -> bool:
        return self._pos.bn == 0 and self._pos.r == self._start_row

    @property
    def dr(self) -> int:
        """The direction of movement."""
        return self._dr

    @property
    def can_promote(self) -> bool:
        """Whether the pawn can be promoted."""
        return self._pos.r == self._promote_row

    def _add_en_passant(self, c: int):
        """Adds an en passant move into the given column."""
        self._add_move(self._pos.r + self._dr, c)
