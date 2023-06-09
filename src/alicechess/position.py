"""
Position, BoardPosition, Move, PieceMove, and PieceMoved classes.
"""

# =============================================================================

from functools import total_ordering
from typing import Iterable, Optional, Self, Tuple

from alicechess.utils import check_brc

# =============================================================================

__all__ = (
    "Position",
    "BoardPosition",
    "Move",
    "PieceMove",
    "PieceMoved",
)

# =============================================================================


def _rc_code(r: int, c: int) -> str:
    row_number = str(8 - r)
    col_letter = "abcdefgh"[c]
    return f"{col_letter}{row_number}"


def _rc_from_code(code: str) -> Tuple[int, int]:
    if len(code) != 2:
        raise ValueError("`code` must be length 2")
    letter, number = code.lower()
    if not number.isdigit():
        raise ValueError(f"Invalid code: not a digit: {number!r}")
    try:
        c = "abcdefgh".index(letter)
    except ValueError:
        raise ValueError(
            f"Invalid code: letter must be a-h (got {letter!r})"
        ) from None
    r = 8 - int(number)
    if not 0 <= r < 8:
        raise ValueError(
            f"Invalid code: number must be within [1, 8] (got {number})"
        )
    return r, c


# =============================================================================


@total_ordering
class _ImmutableParts:
    """A base class for common functions and methods of an immutable
    object made up of "parts".

    The constructor must define the properties:
        _parts: Defines the parts. Must be iterable.
        _str: The __str__ representation.
        _args_tuple: The args as a tuple, as they should appear in the
            __repr__ representation.
    """

    # pylint: disable=no-member

    @classmethod
    def of(cls, obj) -> Self:
        if obj is None:
            return None
        if isinstance(obj, cls):
            return obj
        try:
            args = tuple(obj)
        except TypeError:
            pass
        else:
            # if iterable, use it as args
            return cls(*args)
        raise TypeError(
            f"Cannot create {cls.__name__} from {obj.__class__.__name__}"
        )

    @classmethod
    def to_str(cls, iterable: Iterable[Self], sep: str = " ") -> str:
        """Returns the objs in the given iterable as a string."""
        return sep.join(map(lambda obj: str(cls.of(obj)), iterable))

    def __str__(self):
        return self._str

    def __repr__(self):
        args_str = ", ".join(map(repr, self._args_tuple))
        return f"{self.__class__.__name__}({args_str})"

    def __hash__(self):
        return hash(self._parts)

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self._parts < other._parts
        return self._parts < other

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._parts == other._parts
        return self._parts == other

    def __iter__(self):
        return iter(self._parts)


# =============================================================================


class PositionBase(_ImmutableParts):
    """Position base class."""

    def __init__(self, pos, code):
        self._pos = pos
        self._code = code

        self._parts = self._pos
        self._str = self._code
        self._args_tuple = self._pos

    @classmethod
    def from_code(cls, code: str):
        raise NotImplementedError(
            f"{cls.__name__}: function `from_code()` not implemented"
        )

    @property
    def r(self) -> int:
        """The row."""
        return self._pos[-2]

    @property
    def c(self) -> int:
        """The column."""
        return self._pos[-1]

    @property
    def code(self) -> str:
        """The position code (in algebraic notation)."""
        return self._code


class Position(PositionBase):
    """Represents a position on a single board.

    Properties:
        pos (Tuple[int, int]): The row and column.
        r (int): The row.
        c (int): The column.
        code (str): The position code (in algebraic notation).
    """

    def __init__(self, r, c):
        """Initializes a Position."""
        check_brc(r=r, c=c)
        pos = (r, c)
        code = _rc_code(r, c)
        super().__init__(pos, code)

    @classmethod
    def from_code(cls, code: str) -> "Position":
        """Constructs a Position based on its code.

        Args:
            code (str): The code in algebraic notation (of length 2).

        Raises:
            ValueError: If `code` is invalid.
        """
        r, c = _rc_from_code(code)
        return cls(r, c)

    @property
    def pos(self) -> Tuple[int, int]:
        """The row and column."""
        return self._pos


class BoardPosition(PositionBase):
    """Represents a position on either board.

    Properties:
        pos (Tuple[int, int, int]): The board number, row, and column.
        bn (int): The board number.
        r (int): The row.
        c (int): The column.
        code (str): The position code (in algebraic notation).
    """

    def __init__(self, bn, r, c):
        """Initializes a BoardPosition."""
        check_brc(bn=bn, r=r, c=c)
        pos = (bn, r, c)
        code = "AB"[bn] + _rc_code(r, c)
        super().__init__(pos, code)

    @classmethod
    def from_code(cls, code: str) -> "BoardPosition":
        """Constructs a BoardPosition based on its code.

        Args:
            code (str): The code in algebraic notation (of length 3).

        Raises:
            ValueError: If `code` is invalid.
        """
        if len(code) != 3:
            raise ValueError("`code` must have length 3")
        board = code[0].upper()
        try:
            bn = "AB".index(board)
        except ValueError:
            raise ValueError(
                f"Invalid code: board must be A or B (got {board!r})"
            ) from None
        r, c = _rc_from_code(code[1:])
        return cls(bn, r, c)

    @property
    def pos(self) -> Tuple[int, int, int]:
        """The board number, row, and column."""
        return self._pos

    @property
    def bn(self) -> int:
        """The board number."""
        return self._pos[0]


# =============================================================================


class Move(_ImmutableParts):
    """Represents a move of a piece.

    Properties:
        pos (BoardPosition): The piece position.
        target (Position): The target position.
        capture_pos (BoardPosition): The capture position.
        result_pos (BoardPosition): The piece's resulting position,
            after teleporting.
    """

    def __init__(self, pos: BoardPosition, target: Position):
        """Initializes a Move."""
        self._pos = BoardPosition.of(pos)
        self._target = Position.of(target)
        self._capture_pos = BoardPosition(self._pos.bn, *self._target)
        self._result_pos = BoardPosition(1 - self._pos.bn, *self._target)

        self._parts = (self._pos, self._target)
        self._str = f"{self._pos}-{self._target}"
        self._args_tuple = self._parts

    @property
    def pos(self) -> BoardPosition:
        """The piece position."""
        return self._pos

    @property
    def target(self) -> Position:
        """The target position."""
        return self._target

    @property
    def capture_pos(self) -> BoardPosition:
        """The capture position.

        This is `target` with the board number.
        """
        return self._capture_pos

    @property
    def result_pos(self) -> BoardPosition:
        """The piece's resulting position, after teleporting."""
        return self._result_pos


class PieceMove(Move):
    """Represents a possible move for a piece, which is a Move that
    includes information about the piece.

    Properties:
        pos (BoardPosition): The piece position.
        target (Position): The target position.
        capture_pos (BoardPosition): The capture position.
        result_pos (BoardPosition): The piece's resulting position,
            after teleporting.
        piece_moved (Piece): The piece that is being moved.
    """

    def __init__(self, pos: BoardPosition, target: Position, piece: "Piece"):
        """Initializes a PieceMove."""
        super().__init__(pos, target)

        self._piece_moved = piece

        self._args_tuple = (self._pos, self._target, self._piece_moved)

    @property
    def piece_moved(self) -> "Piece":
        """The piece that was moved."""
        return self._piece_moved


class PieceMoved(PieceMove):
    """Represents a move done by a piece, which is a PieceMove that
    includes information about a possible capture.

    Properties:
        pos (BoardPosition): The piece position.
        target (Position): The target position.
        capture_pos (BoardPosition): The capture position.
        result_pos (BoardPosition): The piece's resulting position,
            after teleporting.
        piece_moved (Piece): The piece that was moved.
        move_captured (bool): Whether the move captured a piece.
        piece_captured (Optional[Piece]): The piece that was captured,
            if given.
    """

    def __init__(
        self,
        pos: BoardPosition,
        target: Position,
        piece: "Piece",
        captured: Optional["Piece"],
    ):
        """Initializes a PieceMoved."""
        super().__init__(pos, target, piece)

        self._piece_moved = piece
        self._move_captured = captured is not None
        self._piece_captured = captured

        self._args_tuple = (
            self._pos,
            self._target,
            self._piece_moved,
            self._piece_captured,
        )

    @property
    def move_captured(self) -> bool:
        """Whether the move captured a piece."""
        return self._move_captured

    @property
    def piece_captured(self) -> Optional["Piece"]:
        """The piece that was captured, if any."""
        return self._piece_captured
