"""
Piece abstract class.
"""

# =============================================================================

from typing import Iterator, Optional, Set

from alicechess.position import BoardPosition, PieceMove, Position
from alicechess.utils import Color, PieceType, check_brc

# =============================================================================

__all__ = ("Piece",)

# =============================================================================


class Piece:
    """Represents a piece.

    Properties:
        id (int): The piece id.
        name (str): The piece name.
        fen_name (str): The piece FEN name.
        type (PieceType): The piece type.
        color (Color): The piece color.
        has_moved (bool): Whether this piece has moved.
        pos (BoardPosition): The piece position.
        num_moves (int): The number of possible moves.
        is_captured (bool): Whether this piece is captured.
        is_threatened (bool): Whether this piece is being threatened on
            the current board. False if not known.

    Methods:
        copy() -> Piece:
            Returns a copy of this piece.

        yield_moves() -> Iterator[PieceMove]
            Yields the possible moves for this piece.
        can_make_move(bn, tr, tc) -> bool
            Returns whether this piece can move to the given position.

        move_to(pos) -> Piece
            Returns a copy of this piece that is moved to the given
            position.
        capture() -> Piece
            Returns a copy of this piece that is captured.
    """

    _type: PieceType = None

    def __init__(
        self,
        piece_id: int,
        color: Color,
        pos: Optional[BoardPosition] = None,
        captured: bool = False,
        has_moved: bool = False,
    ):
        if self._type is None:
            raise RuntimeError(
                f"{self.__class__.__name__} is missing `_type` attribute"
            )
        if pos is None and not captured:
            raise ValueError("Position not given for non-captured piece")
        if captured:
            pos = None

        self._id = piece_id
        self._color = color
        self._name = color.abbr() + self._type.value
        self._fen_name = self._type.value
        if self._color is Color.BLACK:
            self._fen_name = self._fen_name.lower()

        self._pos = BoardPosition.of(pos)
        self._has_moved = has_moved
        self._is_captured = captured
        self._is_threatened = False

        self._moves = None

    def __str__(self):
        attrs = {
            "id": self._id,
            "color": self._color.name,
            "pos": self._pos,
        }
        if self._is_captured:
            attrs["captured"] = True
        attrs_str = " ".join(f"{key}={val}" for key, val in attrs.items())
        return f"{self._type.title()}<{attrs_str}>"

    def __repr__(self):
        args = {
            "piece_id": self._id,
            "color": self._color,
            "pos": repr(self._pos),
            "captured": self._is_captured,
        }
        args_str = ", ".join(f"{key}={val}" for key, val in args.items())
        return f"{self.__class__.__name__}({args_str})"

    @property
    def id(self) -> int:
        """The piece id."""
        return self._id

    @property
    def name(self) -> str:
        """The piece name."""
        return self._name

    @property
    def fen_name(self) -> str:
        """The piece FEN name."""
        return self._fen_name

    @property
    def type(self) -> PieceType:
        """The piece type."""
        return self._type

    @property
    def color(self) -> Color:
        """The piece color."""
        return self._color

    def _check_start_position(self) -> bool:
        """Checks if the current piece position could be a start
        position of the piece.
        """
        raise NotImplementedError()

    @property
    def has_moved(self) -> bool:
        """Whether this piece has moved."""
        if self._has_moved:
            return True
        # also check if this piece is in one of its starting positions
        return not self._check_start_position()

    @property
    def pos(self) -> BoardPosition:
        """The piece position."""
        return self._pos

    @property
    def num_moves(self) -> int:
        """The number of possible moves."""
        return len(self._get_moves())

    @property
    def is_captured(self) -> bool:
        """Whether this piece is captured."""
        return self._is_captured

    @property
    def is_threatened(self) -> bool:
        """Whether this piece is being threatened on the current board.

        False if not known.
        """
        return self._is_threatened

    def copy(self) -> "Piece":
        """Returns a copy of this piece."""
        return self.__class__(
            self._id,
            self._color,
            self._pos,
            self._is_captured,
            self._has_moved,
        )

    def _set_possible_moves(self, moves: Set[Position]):
        """Sets the possible moves of this piece. Should only be called
        by a `MovesCalculator` instance.
        """
        if self._is_captured:
            raise RuntimeError("Cannot set possible moves for captured piece")
        self._moves = []
        for target in moves:
            self._moves.append(PieceMove(self._pos, target, self))
        self._moves.sort()

    def _add_move(self, tr: int, tc: int):
        """Adds the given move."""
        if self._moves is None:
            raise ValueError(
                f"{self._type.title()} has not calculated its possible moves"
            )
        check_brc(tr=tr, tc=tc)
        self._moves.append(PieceMove(self._pos, (tr, tc), self))
        self._moves.sort()

    def _mark_threatened(self, is_threatened: bool):
        """Marks the current piece as being threatened or not. Should
        only be called by a `MovesCalculator` instance.
        """
        if self._is_captured:
            raise RuntimeError("Cannot mark threatened for a captured piece")
        self._is_threatened = is_threatened

    def _set_moved(self):
        """Sets this piece as having moved."""
        self._has_moved = True

    def _get_moves(self):
        if self._is_captured:
            raise RuntimeError("Cannot get moves for captured piece")
        if self._moves is None:
            raise RuntimeError(
                f"{self._type.title()} has not calculated its possible moves"
            )
        return self._moves

    def yield_moves(self) -> Iterator[PieceMove]:
        """Yields the possible moves for this piece."""
        return iter(self._get_moves())

    def can_make_move(self, bn: int, tr: int, tc: int) -> bool:
        """Returns whether this piece can move to the given position.

        Args:
            bn (int): The board number.
            tr (int): The target row.
            tc (int): The target column.

        Raises:
            ValueError:
                If `bn` is not 0 or 1.
                If `tr` and `tc` are not bounded within [0, 7].

        Returns:
            bool: Whether this piece can move to the given position.
        """
        check_brc(bn=bn, tr=tr, tc=tc)
        if bn != self._pos.bn:
            # can't move to somewhere on the other board
            return False
        return (tr, tc) in (move.target for move in self._get_moves())

    def move_to(self, pos: BoardPosition) -> "Piece":
        """Returns a copy of this piece that is moved to the given
        position.

        Also changes `has_moved` to True.
        """
        if self._is_captured:
            raise RuntimeError("Cannot move a captured piece")
        # can't be captured, so leave it as false
        return self.__class__(self._id, self._color, pos, has_moved=True)

    def capture(self) -> "Piece":
        """Returns a copy of this piece that is captured."""
        if self._is_captured:
            return self
        return self.__class__(
            self._id, self._color, captured=True, has_moved=self._has_moved
        )
