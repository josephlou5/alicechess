"""
King piece.
"""

# =============================================================================

from alicechess.pieces.piece import Piece
from alicechess.utils import Color, PieceType

# =============================================================================


class King(Piece):
    """King piece.

    Properties:
        can_castle_left (bool): Whether the king can castle to the left
            (queenside).
        left_rook_col (Optional[int]): The column the left rook castles
            to, if the king can castle with it.
        can_castle_right (bool): Whether the king can castle to the
            right (kingside).
        right_rook_col (Optional[int]): The column the right rook
            castles to, if the king can castle with it.
    """

    _type = PieceType.KING

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._left_rook_col = None
        self._right_rook_col = None

        if self._color is Color.WHITE:
            start_row = 7
        else:
            start_row = 0
        # king is always on the right (for this particular board setup)
        self._start_pos = (0, start_row, 4)

    def _check_start_position(self) -> bool:
        return self._pos == self._start_pos

    @property
    def can_castle_left(self) -> bool:
        """Whether the king can castle to the left (queenside)."""
        return self._left_rook_col is not None

    @property
    def left_rook_col(self):
        """The column the left rook castles to, if the king can castle
        with it.
        """
        return self._left_rook_col

    @property
    def can_castle_right(self) -> bool:
        """Whether the king can castle to the right (kingside)."""
        return self._right_rook_col is not None

    @property
    def right_rook_col(self):
        """The column the right rook castles to, if the king can castle
        with it.
        """
        return self._right_rook_col

    def _add_castle(self, rook_c: int, king_c: int):
        """Adds a castle to the given column."""
        if self._moves is None:
            raise RuntimeError("King has not calculated its possible moves")
        # since the board is constructed with white on the bottom,
        # technically the castle columns are always fixed
        _, kr, kc = self._pos
        if king_c < kc:
            # left castle
            self._left_rook_col = rook_c
        else:
            # right castle
            self._right_rook_col = rook_c
        # add the move
        self._add_move(kr, king_c)
