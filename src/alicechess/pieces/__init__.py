"""
Pieces submodule.
"""

# =============================================================================

import typing as _t

from alicechess.pieces.king import King
from alicechess.pieces.pawn import Pawn
from alicechess.pieces.piece import Piece
from alicechess.utils import Color, PieceType, PromoteType

# =============================================================================

__all__ = (
    "Piece",
    "King",
    "Queen",
    "Rook",
    "Knight",
    "Bishop",
    "Pawn",
    "make_promoted",
)

# =============================================================================


def _make_simple_piece(piece_type, rows, columns=None) -> _t.Type[Piece]:
    """Makes a piece."""
    # pylint: disable=missing-class-docstring

    class Subclass(Piece):
        _type = piece_type

        def _check_start_position(self) -> bool:
            if self._pos.bn != 0:
                return False
            if self._color is Color.WHITE:
                row = rows[0]
            else:
                row = rows[1]
            if self._pos.r != row:
                return False
            if columns is not None and self._pos.c not in columns:
                return False
            return True

    piece_name = piece_type.title()
    Subclass.__name__ = piece_name
    Subclass.__doc__ = f"{piece_name} piece."

    return Subclass


# queen is always on the left for this particular board setup
Queen = _make_simple_piece(PieceType.QUEEN, (7, 0), (3,))
Rook = _make_simple_piece(PieceType.ROOK, (7, 0), (0, 7))
Knight = _make_simple_piece(PieceType.KNIGHT, (7, 0), (1, 6))
Bishop = _make_simple_piece(PieceType.BISHOP, (7, 0), (2, 5))

# =============================================================================


def make_promoted(
    pawn: Pawn, promote_type: PromoteType
) -> _t.Union[Queen, Rook, Knight, Bishop]:
    PROMOTE_CLASSES = {
        PromoteType.QUEEN: Queen,
        PromoteType.ROOK: Rook,
        PromoteType.KNIGHT: Knight,
        PromoteType.BISHOP: Bishop,
    }
    return PROMOTE_CLASSES[promote_type](
        pawn.id, pawn.color, pawn.pos, has_moved=pawn.has_moved
    )
