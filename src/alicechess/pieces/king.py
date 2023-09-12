"""
King piece.
"""

# =============================================================================

from typing import Optional

from alicechess.pieces.piece import Piece
from alicechess.position import BoardPosition
from alicechess.utils import Color, PieceType

# =============================================================================


class King(Piece):
    """King piece."""

    _type = PieceType.KING

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self._color is Color.WHITE:
            start_row = 7
        else:
            start_row = 0
        # king is always on the right (for this particular board setup)
        self._start_pos = (0, start_row, 4)

    def is_at_start_pos(self, pos: Optional[BoardPosition] = None) -> bool:
        return (pos or self._pos) == self._start_pos

    def _add_castle(self, c: int):
        """Adds a castle to the given column."""
        if self._moves is None:
            raise RuntimeError("King has not calculated its possible moves")
        self._add_move(self._pos.r, c)
