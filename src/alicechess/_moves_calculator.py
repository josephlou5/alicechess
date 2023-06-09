"""
MovesCalculator class.
"""

# =============================================================================

from functools import partial
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from alicechess.pieces import King, Pawn, Piece, Rook
from alicechess.position import BoardPosition, Position
from alicechess.utils import Color, PieceType, check_brc, check_brc_bool

# =============================================================================

BoardDict = Dict[BoardPosition, Piece]

# =============================================================================

STRAIGHT_DIRS = (
    (0, -1),  # left
    (-1, 0),  # up
    (0, 1),  # right
    (1, 0),  # down
)

DIAGONAL_DIRS = (
    (-1, -1),  # up left
    (-1, 1),  # up right
    (1, 1),  # down right
    (1, -1),  # down left
)

ALL_DIRS = STRAIGHT_DIRS + DIAGONAL_DIRS

KNIGHT_MOVES = (
    (-1, -2),  # left up
    (-2, -1),  # up left
    (-2, 1),  # up right
    (-1, 2),  # right up
    (1, 2),  # right down
    (2, 1),  # down right
    (2, -1),  # down left
    (1, -2),  # left down
)


def _yield_pos(directions, pr, pc, steps=None) -> Iterator[Tuple[int, int]]:
    for dr, dc in directions:
        r = pr
        c = pc
        i = 0
        while steps is None or i < steps:
            r += dr
            c += dc
            if not check_brc_bool(r=r, c=c):
                break
            stop = yield r, c
            if stop:
                # last yield for send
                yield None
                break
            i += 1


yield_straight_pos = partial(_yield_pos, STRAIGHT_DIRS)
yield_diagonal_pos = partial(_yield_pos, DIAGONAL_DIRS)
yield_all_dir_pos = partial(_yield_pos, ALL_DIRS)
yield_knight_pos = partial(_yield_pos, KNIGHT_MOVES, steps=1)


POS_GEN_FUNCS = {
    PieceType.KING: partial(yield_all_dir_pos, steps=1),
    PieceType.QUEEN: yield_all_dir_pos,
    PieceType.ROOK: yield_straight_pos,
    PieceType.KNIGHT: yield_knight_pos,
    PieceType.BISHOP: yield_diagonal_pos,
}

# =============================================================================


def _get(board: BoardDict, bn: int, r: int, c: int):
    return board.get((bn, r, c), None)


# =============================================================================


def _yield_threatened_by(
    board: BoardDict, by_color: Color, bn: int, r: int, c: int
) -> Iterator[Piece]:
    """Yields the pieces that the given position is threatened by."""
    check_brc(bn, r, c)

    piece_at_pos = _get(board, bn, r, c)
    if piece_at_pos is not None:
        if piece_at_pos.color is by_color:
            # own piece can't be threatened
            return

    # check knight positions
    for tr, tc in yield_knight_pos(r, c):
        piece = _get(board, bn, tr, tc)
        if piece is None or piece.color is not by_color:
            continue
        if piece.type is PieceType.KNIGHT:
            yield piece

    # check pawn positions
    if by_color is Color.WHITE:
        # threaten from bottom
        dr = 1
    else:
        # threaten from top
        dr = -1
    for dc in (-1, 1):
        piece = _get(board, bn, r + dr, c + dc)
        if piece is None or piece.color is not by_color:
            continue
        if piece.type is PieceType.PAWN:
            yield piece

    # check king positions
    for tr, tc in POS_GEN_FUNCS[PieceType.KING](r, c):
        piece = _get(board, bn, tr, tc)
        if piece is None or piece.color is not by_color:
            continue
        if piece.type is PieceType.KING:
            yield piece

    # check straights and diagonals
    for pos_gen_func, piece_types in (
        (yield_straight_pos, (PieceType.QUEEN, PieceType.ROOK)),
        (yield_diagonal_pos, (PieceType.QUEEN, PieceType.BISHOP)),
    ):
        pos_gen = pos_gen_func(r, c)
        for tr, tc in pos_gen:
            piece = _get(board, bn, tr, tc)
            if piece is None:
                continue
            if piece.color is by_color and piece.type in piece_types:
                yield piece
            # done with this direction
            pos_gen.send(True)


def _is_threatened(
    board: BoardDict, by_color: Color, bn: int, r: int, c: int
) -> bool:
    try:
        next(_yield_threatened_by(board, by_color, bn, r, c))
        return True
    except StopIteration:
        # nothing yielded
        return False


# =============================================================================


class MovesCalculator:
    """Calculates the possible moves for a given board state.

    Methods:
        num_moves(color) -> int
            Returns the number of moves for the given color.
        is_in_check(color) -> bool
            Returns whether the given color is in check.
    """

    def __init__(
        self,
        board: BoardDict,
        kings: Tuple[King],
        unmoved_rooks: Tuple[Sequence[Rook]],
        en_passant_pawn: Optional[Pawn] = None,
    ):
        self._board = board
        self._kings = tuple(kings)
        unmoved_rooks = tuple(map(tuple, unmoved_rooks))

        pawns: Tuple[List[Pawn]] = ([], [])
        for piece in self._board.values():
            if piece.type is PieceType.PAWN:
                pawns[piece.color.value].append(piece)

        self._in_check = tuple(
            _is_threatened(self._board, king.color.other(), *king.pos)
            for king in self._kings
        )
        if self._in_check == (True, True):
            raise ValueError("Both kings are in check")
        self._num_moves = [0, 0]

        # calculate all the possible moves
        for piece in self._board.values():
            self._calc_possible(piece)

        # check for castling
        for king, in_check, rooks in zip(
            self._kings, self._in_check, unmoved_rooks
        ):
            if king.has_moved:
                continue
            if in_check:
                continue
            if len(rooks) == 0:
                continue
            enemy_color = king.color.other()
            bn, kr, kc = king.pos
            for rook in rooks:
                rc = rook.pos.c
                if rc < kc:
                    # left rook: king will move to the left
                    dc = -1
                else:  # kc < rc
                    # right rook: king will move to the right
                    dc = 1
                valid_castle = True
                # check that the spaces in the middle are empty
                c = kc + dc
                while c != rc:
                    if (bn, kr, c) in self._board:
                        # there's a piece there on this board
                        valid_castle = False
                        break
                    if abs(c - kc) <= 2:
                        # the spaces being landed on must be empty on
                        # the other board as well
                        if (1 - bn, kr, c) in self._board:
                            valid_castle = False
                            break
                    c += dc
                if not valid_castle:
                    continue
                # check that the spaces the king moves through are not
                # threatened on this board
                c = kc
                for _ in range(2):
                    c += dc
                    if _is_threatened(self._board, enemy_color, bn, kr, c):
                        valid_castle = False
                        break
                if not valid_castle:
                    continue
                # check that the king does not teleport into check on
                # the other board
                king_c = kc + dc + dc
                if _is_threatened(
                    self._board, enemy_color, 1 - bn, kr, king_c
                ):
                    continue
                # king moves two spaces
                king._add_castle(rook_c=kc + dc, king_c=kc + dc + dc)

        # check for en passant
        if en_passant_pawn is not None:
            if en_passant_pawn.type is not PieceType.PAWN:
                raise ValueError("Given en passant piece is not a pawn")
            pbn, pr, pc = en_passant_pawn.pos
            if pbn != 1:
                raise ValueError("Given en passant pawn is not on Board B")
            # see if any of the enemy's pawns can perform en passant
            for pawn in pawns[en_passant_pawn.color.other().value]:
                bn, r, c = pawn.pos
                if bn != 1:
                    # cannot capture a piece on the other board
                    continue
                if not (r == pr and abs(c - pc) == 1):
                    # pawn is not adjacent to advanced pawn
                    continue
                capture_r = r + pawn.dr
                capture_pos = (capture_r, pc)
                if any((bn, *capture_pos) in self._board for bn in range(2)):
                    # there's a piece there; no en passant
                    continue
                if self._move_in_check(
                    pawn.pos, capture_pos, en_passant=(pr, pc)
                ):
                    continue
                pawn._add_en_passant(pc)

        for piece in self._board.values():
            piece._mark_threatened(False)
            self._num_moves[piece.color.value] += piece.num_moves
        for piece in self._board.values():
            for move in piece.yield_moves():
                threatened_piece = self._get(*move.capture_pos)
                if threatened_piece is not None:
                    threatened_piece._mark_threatened(True)

    def _get(self, bn: int, r: int, c: int) -> Optional[Piece]:
        return _get(self._board, bn, r, c)

    def num_moves(self, color: Color) -> int:
        """Returns the number of moves for the given color."""
        return self._num_moves[color.value]

    def is_in_check(self, color: Color) -> bool:
        """Returns whether the given color is in check."""
        return self._in_check[color.value]

    def _move_in_check(
        self,
        pos: BoardPosition,
        target: Position,
        en_passant: Optional[Position] = None,
    ):
        pos = BoardPosition.of(pos)
        tr, tc = target
        here_target_pos = (pos.bn, tr, tc)
        there_target_pos = (1 - pos.bn, tr, tc)

        moving = self._get(*pos)
        if moving is None:
            raise ValueError(f"No piece at position {pos} {pos.pos}")

        # make temp copy board (no need to copy pieces because not
        # changing them)
        board = dict(self._board)

        # check move validity
        if en_passant is None:
            captured = _get(board, *here_target_pos)
            if captured is not None:
                if captured.type is PieceType.KING:
                    raise ValueError("Move captures a king")
                if captured.color is moving.color:
                    raise ValueError("Move captures own piece")
        else:
            # capture the en passant piece
            captured = board.pop((pos.bn, *en_passant), None)
            if captured is None:
                raise ValueError("Given en passant position is blank")
            if captured.type is not PieceType.PAWN:
                raise ValueError("Cannot perform en passant on a non-pawn")
            if captured.color is moving.color:
                raise ValueError("En passant captures own piece")
        other_board = _get(board, *there_target_pos)
        if other_board is not None:
            raise ValueError("Move squashes a piece on the other board")

        enemy_color = moving.color.other()
        king = self._kings[moving.color.value]
        moving_king = moving is king

        # make sure move is valid on current board
        board[here_target_pos] = board.pop(pos).move_to(here_target_pos)
        if moving_king:
            check_pos = here_target_pos
        else:
            check_pos = king.pos
        if moving_king or pos.bn == king.pos.bn:
            # if the king is moving, can't move into check
            # otherwise, if on the same board as the king, can't let the
            # king be in check
            if _is_threatened(board, enemy_color, *check_pos):
                return True
        # make sure move is valid after teleporting
        board[there_target_pos] = board.pop(here_target_pos).move_to(
            there_target_pos
        )
        if moving_king:
            check_pos = there_target_pos
        else:
            check_pos = king.pos
        if _is_threatened(board, enemy_color, *check_pos):
            return True

        return False

    def _calc_possible_pawn(self, piece: Pawn):
        bn, pr, pc = piece.pos
        moves = set()

        def check_pos(r, c):
            if not check_brc_bool(r=r, c=c):
                return
            this_board = self._get(bn, r, c)
            if this_board is not None:
                return
            other_board = self._get(1 - bn, r, c)
            if other_board is not None:
                return
            if self._move_in_check(piece.pos, (r, c)):
                return
            moves.add(Position(r, c))

        r = pr + piece.dr

        if not check_brc_bool(r=r):
            # row is out of bounds; the pawn is on the promotion row
            return moves

        # forward
        c = pc
        check_pos(r, c)
        if not piece.has_moved and self._get(bn, r, c) is None:
            # check double forward
            check_pos(r + piece.dr, c)

        # diagonal capture
        for dc in (-1, 1):
            c = pc + dc
            if not check_brc_bool(c=c):
                continue
            front_diag = self._get(bn, r, c)
            if front_diag is None:
                # must have a piece there
                continue
            this_board = self._get(bn, r, c)
            if this_board is not None:
                if this_board.type is PieceType.KING:
                    # can't capture a king
                    continue
                if this_board.color is piece.color:
                    # can't capture your own piece
                    continue
            other_board = self._get(1 - bn, r, c)
            if other_board is not None:
                # can't replace on other board
                continue
            if self._move_in_check(piece.pos, (r, c)):
                continue
            moves.add(Position(r, c))

        return moves

    def _calc_possible(self, piece: Piece):
        if self._get(*piece.pos) is not piece:
            raise ValueError(
                f"Piece {piece.name!r} is not at the proper position "
                f"({piece.pos}) in the board"
            )
        if piece.type is PieceType.PAWN:
            moves = self._calc_possible_pawn(piece)
        else:
            bn, pr, pc = piece.pos
            moves = set()
            pos_gen = POS_GEN_FUNCS[piece.type](pr, pc)
            for r, c in pos_gen:
                this_board = self._get(bn, r, c)
                if this_board is not None:
                    # done with this direction
                    pos_gen.send(True)
                    if this_board.type is PieceType.KING:
                        # can't capture a king
                        continue
                    if this_board.color is piece.color:
                        # can't capture your own piece
                        continue
                other_board = self._get(1 - bn, r, c)
                if other_board is not None:
                    # can't replace on other board
                    continue
                if self._move_in_check(piece.pos, (r, c)):
                    continue
                moves.add(Position(r, c))
        piece._set_possible_moves(moves)  # pylint: disable=protected-access
