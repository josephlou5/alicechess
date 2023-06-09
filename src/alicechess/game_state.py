"""
GameState class.
"""

# =============================================================================

import math
from itertools import count, zip_longest
from typing import Dict, Iterable, Iterator, Optional, Self, Type

from alicechess import pieces
from alicechess._moves_calculator import BoardDict, MovesCalculator
from alicechess.pieces import Piece, make_promoted
from alicechess.player import AnyPlayer
from alicechess.position import Move, PieceMove, PieceMoved, Position
from alicechess.utils import Color, EndGameState, PieceType, PromoteType

# =============================================================================

__all__ = ("GameState",)

# =============================================================================

_PRIVATE_game_state_constructor_key = object()


class GameState:  # pylint: disable=too-many-public-methods
    """Immutable state of a game.

    Includes board state, previous moves, captured pieces, possible
    moves, and end game state.

    Constructors:
        GameState.new(*, white, black)
            Initializes the first GameState of a game.
        GameState.from_fen(fen, *, white, black)
            Initializes a GameState from a FEN string, using the given
            players.

    Properties:
        id (int): The game state id.

        white (Player): The white player.
        black (Player): The black player.

        prev (Optional[GameState]): The previous GameState, or None if
            this is the first state.
        move (Optional[PieceMoved]): The move from the previous
            GameState, or None if this is the first state.

        current_color (Color): The color of the current player.
        current_player (Player): The current player.

        half_move_clock (int): The number of half-moves since the last
            capture or the last pawn moved.
        num_moves (int): The number of full moves played in the entire
            game.

    Methods:
        fen() -> str
            Returns the FEN representation of the game.
        board_to_str(empty=" .") -> str
            Returns a string representation of the board.
        moves_to_str(columns=4, captured_empty=True) -> str
            Returns a string representation of the moves for each piece.

        is_game_over() -> bool
            Returns whether the game is over (checkmate, stalemate, or
            draw).
        is_in_checkmate() -> bool
            Returns whether the current player is in checkmate.
        winner() -> Optional[Color]
            Returns the winner of the game (for checkmate).
        is_in_stalemate() -> bool
            Returns whether the current player is in stalemate.
        is_kings_draw() -> bool
            Returns whether the game is a draw by only having kings.
        is_draw() -> bool
            Returns whether the game is a draw (by the fifty move rule).

        is_in_check() -> bool
            Returns whether the current player is in check.
        needs_promotion() -> bool
            Returns whether the state is waiting for a promotion for the
            last moved pawn.
        promote(promote_type) -> GameState
            Promotes the promoting pawn.

        yield_all_pieces() -> Iterator[Piece]
            Yields all the pieces.
        yield_player_pieces() -> Iterator[Piece]
            Yields all the pieces for the current player.
        yield_player_moves() -> Iterator[PieceMove]
            Yields all the possible moves for the current player.
        num_captured() -> int
            Returns the number of captured pieces.
        yield_captured() -> Iterator[Piece]
            Yields the captured pieces.

        get_piece(bn, r, c) -> Optional[Piece]
            Gets the piece at the given position.

        make_move(move) -> GameState
            Makes the given move.
        step() -> GameState
            Advances a step of the game.
        run() -> GameState
            Runs the game until it's over.

        restart() -> GameState
            Returns the starting state with the same players.
    """

    __game_state_counter = count()

    def __init__(
        self,
        key,
        *,
        white: AnyPlayer,
        black: AnyPlayer,
        current_color: Color,
        prev: Optional[Self],
        move: Optional[Move],
        piece_captured: Optional[Piece],
        en_passant_pawn: Optional[Piece],
        half_move_clock: int,
        num_moves: int,
        board: BoardDict,
        captured: Iterable[Piece],
    ):
        """Initializes a GameState. Should only be called internally."""
        if key is not _PRIVATE_game_state_constructor_key:
            raise RuntimeError(
                "You should not be calling the GameState constructor"
            )

        if white.color is not Color.WHITE:
            raise ValueError("`white` does not have color `Color.WHITE`")
        if black.color is not Color.BLACK:
            raise ValueError("`black` does not have color `Color.BLACK`")
        self._white = white
        self._black = black
        self._current_color = current_color

        # cache the resulting game state whenever someone tries to make
        # a move, in case a bot wants to look ahead
        self._moves: Dict[Move, GameState] = {}
        # cache the resulting game state whenever a pawn is promoted
        self._promotions: Dict[PromoteType, GameState] = {}

        if (prev is None) != (move is None):
            raise ValueError("`prev` and `move` must both be None or not None")

        if prev is None:
            self._first_state = self
        else:
            self._first_state = prev._first_state
        self._prev = prev

        self._half_move_clock = half_move_clock
        self._num_moves = num_moves

        self._captured = tuple(captured)

        # construct board
        self._board: BoardDict = {}
        self._kings = [None, None]
        seen_piece_ids = set()
        unmoved_rooks = ([], [])
        for piece in board.values():
            if piece.id in seen_piece_ids:
                raise ValueError(f"Multiple pieces with id: {piece.id}")
            seen_piece_ids.add(piece.id)
            if piece.pos in self._board:
                raise ValueError(f"Multiple pieces at position {piece.pos}")
            self._board[piece.pos] = piece
            if piece.type is PieceType.KING:
                self._kings[piece.color.value] = piece
            elif piece.type is PieceType.ROOK:
                if not piece.has_moved:
                    unmoved_rooks[piece.color.value].append(piece)

        # validate last move
        piece_moved = None
        self._promoting_pawn = None
        move = Move.of(move)
        if move is None:
            self._move = None
        else:
            if self.get_piece(*move.pos) is not None:
                raise ValueError(
                    "Invalid move from prev: start position still has a piece"
                )
            piece_moved = self.get_piece(*move.result_pos)
            if piece_moved is None:
                raise ValueError(
                    "Invalid move from prev: end position is empty"
                )
            if piece_moved.type is PieceType.PAWN:
                if piece_moved.can_promote:
                    self._promoting_pawn = piece_moved

            # change from `Move` to `PieceMoved`
            self._move = PieceMoved(*move, piece_moved, piece_captured)

        # validate kings
        if self._kings == [None, None]:
            raise ValueError("Missing both kings")
        for i, king in enumerate(self._kings):
            if king is None:
                raise ValueError(f"Missing {Color(i).name.lower()} king")
        # make sure kings are not next to each other
        # board number doesn't matter, since being next to each other on
        # opposite boards meant someone was able to go close on the same
        # board, which is still invalid
        _, r0, c0 = self._kings[0].pos
        _, r1, c1 = self._kings[1].pos
        if abs(r0 - r1) <= 1 and abs(c0 - c1) <= 1:
            raise ValueError("Kings are next to each other")

        self._id = next(self.__game_state_counter)

        # compute fen representation
        # forsyth-edwards notation (FEN): https://www.chess.com/terms/fen-chess
        fen = []

        def color_case(color, value):
            if color is Color.WHITE:
                return value.upper()
            else:  # color is Color.BLACK
                return value.lower()

        # piece placements
        placements = []
        for bn in range(2):
            for r in range(8):
                rank = []
                empty = 0
                for c in range(8):
                    piece = self.get_piece(bn, r, c)
                    if piece is None:
                        empty += 1
                        continue
                    if empty > 0:
                        rank.append(str(empty))
                        empty = 0
                    rank.append(piece.fen_name)
                if empty > 0:
                    rank.append(str(empty))
                placements.append("".join(rank))
        fen.append("/".join(placements))
        # active color
        fen.append(self._current_color.abbr().lower())
        # castling rights
        castling = []
        for color in (Color.WHITE, Color.BLACK):
            king = self._kings[color.value]
            if king.has_moved:
                continue
            kc = king.pos.c
            kingside = False
            queenside = False
            for rook in unmoved_rooks[color.value]:
                rc = rook.pos.c
                if rc < kc:  # left rook: queenside
                    queenside = True
                else:  # right rook: kingside
                    kingside = True
            if kingside:
                # kingside
                castling.append(color_case(color, "K"))
            if queenside:
                # queenside
                castling.append(color_case(color, "Q"))
        if len(castling) == 0:
            fen.append("-")
        else:
            fen.append("".join(castling))
        # en passant target
        if en_passant_pawn is None:
            fen.append("-")
        else:
            _, r, c = en_passant_pawn.pos
            r -= en_passant_pawn.dr
            fen.append(Position(r, c).code)
        # half move clock
        fen.append(str(self._half_move_clock))
        # full move number
        fen.append(str(self._num_moves))
        # combine
        self._fen = " ".join(fen)

        if len(self._board) == 2:
            # only two kings are left
            self._is_in_check = False
            self._end_game_state = EndGameState.ONLY_KINGS_DRAW
            return
        if self._half_move_clock >= 100:
            # 50 move rule
            self._is_in_check = False
            self._end_game_state = EndGameState.FIFTY_MOVE_DRAW
            return

        # calculate all the possible moves
        calculator = MovesCalculator(
            self._board, self._kings, unmoved_rooks, en_passant_pawn
        )

        self._is_in_check = calculator.is_in_check(self._current_color)

        # determine end game state for current player
        no_more_moves = calculator.num_moves(self._current_color) == 0
        if no_more_moves:
            if self._is_in_check:
                self._end_game_state = EndGameState.CHECKMATE
            else:
                self._end_game_state = EndGameState.STALEMATE
        else:
            self._end_game_state = None

    def debug(self):
        print("=" * 50)
        print(self.fen())
        print(self.board_to_str())
        print(self.moves_to_str())
        if self.is_game_over():
            print("end game state:", self._end_game_state)
            if self.is_in_checkmate():
                print("winner:", self.winner())
        else:
            print("in check:", self.is_in_check())

    @classmethod
    def new(cls, *, white: Type[AnyPlayer], black: Type[AnyPlayer]) -> Self:
        """Initializes the first GameState of a game."""
        initial_fen = (
            # initial board position
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR/8/8/8/8/8/8/8/8",
            # white goes first
            "w",
            # all pieces can castle
            "KQkq",
            # no en passant
            "-",
            # no moves yet
            "0",
            "0",
        )
        return cls.from_fen(" ".join(initial_fen), white=white, black=black)

    @classmethod
    def from_fen(
        cls, fen: str, *, white: Type[AnyPlayer], black: Type[AnyPlayer]
    ) -> Self:
        """Initializes a GameState from a FEN string, using the given
        players.
        """

        white_player = white(Color.WHITE)
        black_player = black(Color.BLACK)

        fen_parts = fen.split()  # split by spaces
        if len(fen_parts) != 6:
            raise ValueError(f"`fen` expects 6 fields; got {len(fen_parts)}")
        (
            placements_str,
            active_color,
            castling_rights,
            en_passant_target,
            half_move_clock_str,
            full_move_number_str,
        ) = fen_parts

        # get pieces
        placements = placements_str.split("/")
        if len(placements) != 16:
            raise ValueError(
                "`fen` piece placements expects 16 ranks; "
                f"got {len(placements)}"
            )
        PIECE_CLASSES: Dict[str, Type[Piece]] = {
            "K": pieces.King,
            "Q": pieces.Queen,
            "R": pieces.Rook,
            "N": pieces.Knight,
            "B": pieces.Bishop,
            "P": pieces.Pawn,
        }
        piece_id = count()
        board: BoardDict = {}
        kings = [None, None]
        rooks = ([], [])
        for i, rank in enumerate(placements):
            bn, r = divmod(i, 8)
            num_files = 0
            for c in rank:
                # allow multiple digits in a row, just because i'm not
                # gonna be super strict about this
                if c.isdigit():
                    num_files += int(c)
                    continue
                piece_cls = PIECE_CLASSES.get(c.upper(), None)
                if piece_cls is None:
                    raise ValueError(f"Rank {i}: invalid piece symbol: {c!r}")
                color = Color.WHITE if c.isupper() else Color.BLACK
                piece = piece_cls(next(piece_id), color, (bn, r, num_files))
                board[piece.pos] = piece
                num_files += 1

                if piece.type is PieceType.KING:
                    kings[color.value] = piece
                elif piece.type is PieceType.ROOK:
                    rooks[color.value].append(piece)
            if num_files < 8:
                raise ValueError(f"Rank {i} has less than 8 files: {rank}")
            elif num_files > 8:
                raise ValueError(f"Rank {i} has more than 8 files: {rank}")

        # get active color
        if active_color == "w":
            current_color = Color.WHITE
        elif active_color == "b":
            current_color = Color.BLACK
        else:
            raise ValueError(f"Invalid active color symbol: {active_color!r}")

        # castling rights
        can_castle = ([False, False], [False, False])
        if castling_rights == "-":
            # nobody can castle
            pass
        else:
            for c in castling_rights:
                color = Color.WHITE if c.isupper() else Color.BLACK
                if c.upper() == "K":
                    # kingside castle
                    index = 1
                elif c.upper() == "Q":
                    # queenside castle
                    index = 0
                else:
                    raise ValueError(f"Invalid castling symbol: {c!r}")
                can_castle[color.value][index] = True
        for color in Color:
            # pylint: disable=protected-access
            ability = can_castle[color.value]
            if ability == [True, True]:
                # can castle on both sides, so leave the pieces
                # untouched
                continue
            king = kings[color.value]
            if king is None:
                # ignore; the error will come up later
                continue
            if ability == [False, False]:
                # can't castle on either side, so just say the king
                # moved
                king._set_moved()
                continue
            kc = king.pos.c
            for rook in rooks[color.value]:
                if rook.has_moved:
                    # not in an initial position, so just say it moved
                    rook._set_moved()
                    continue
                rc = rook.pos.c
                if rc < kc:  # left rook: queenside
                    index = 0
                else:  # right rook:
                    index = 1
                if not ability[index]:
                    # can't castle this way
                    rook._set_moved()

        # get en passant pawn
        if en_passant_target == "-":
            en_passant_pawn = None
        else:
            try:
                en_passant_pos = Position.from_code(en_passant_target)
            except ValueError as e:
                raise ValueError(
                    f"Invalid en passant target: {en_passant_target!r}"
                ) from e
            r, c = en_passant_pos
            # check for a pawn that is right in front of this position
            if r == 2:
                pawn = board.get((1, r + 1, c), None)
            elif r == 5:
                pawn = board.get((1, r - 1, c), None)
            else:
                raise ValueError(
                    "Invalid en passant target: rank must be 3 (for black) or "
                    "6 (for white)"
                )
            if pawn is None:
                raise ValueError(
                    f"No pawn found for en passant target: {en_passant_target}"
                )
            if pawn.type is not PieceType.PAWN:
                raise ValueError(
                    f"Piece for en passant target {en_passant_pos} is not a "
                    f"pawn: {pawn.type.title()} at {pawn.pos}"
                )
            # check that the pawn could have made this move in the last
            # turn
            if any(
                pos in board
                for pos in (
                    # something was blocking on the original board
                    (0, r, c),
                    # something else is in the original position
                    (0, r - pawn.dr, c),
                    (1, r - pawn.dr, c),
                )
            ):
                raise ValueError(
                    f"En passant pawn at {pawn.pos} could not have advanced "
                    "two squares in the last move"
                )
            en_passant_pawn = pawn

        if not half_move_clock_str.isdigit():
            raise ValueError(
                f"Halfmove clock is not an integer: {half_move_clock_str!r}"
            )
        half_move_clock = int(half_move_clock_str)
        if not full_move_number_str.isdigit():
            raise ValueError(
                f"Fullmove number is not an integer: {full_move_number_str!r}"
            )
        num_moves = int(full_move_number_str)

        return cls(
            _PRIVATE_game_state_constructor_key,
            white=white_player,
            black=black_player,
            current_color=current_color,
            # we don't know anything about the previous moves
            prev=None,
            move=None,
            piece_captured=None,
            en_passant_pawn=en_passant_pawn,
            half_move_clock=half_move_clock,
            num_moves=num_moves,
            board=board,
            # we don't know anything about the captured pieces
            captured=[],
        )

    def __str__(self) -> str:
        return self._fen

    @property
    def id(self) -> int:
        """The game state id."""
        return self._id

    @property
    def white(self) -> AnyPlayer:
        """The white player."""
        return self._white

    @property
    def black(self) -> AnyPlayer:
        """The black player."""
        return self._black

    @property
    def prev(self) -> Optional[Self]:
        """The previous GameState, or None if this is the first state."""
        return self._prev

    @property
    def move(self) -> Optional[PieceMoved]:
        """The move from the previous GameState, or None if this is the
        first state.
        """
        return self._move

    @property
    def current_color(self) -> Color:
        """The color of the current player."""
        return self._current_color

    @property
    def current_player(self) -> AnyPlayer:
        """The current player."""
        if self._current_color is Color.WHITE:
            return self._white
        else:
            return self._black

    @property
    def half_move_clock(self) -> int:
        """The number of half-moves since the last capture or the last
        pawn moved.
        """
        return self._half_move_clock

    @property
    def num_moves(self):
        """The number of full moves played in the entire game."""
        return self._num_moves

    def fen(self) -> str:
        """Returns the FEN representation of the game.

        Since Alice Chess has two boards, the piece placement portion is
        doubled in length, where the first 8 ranks refer to Board A (on
        the left) and the last 8 ranks refer to Board B (on the right).
        """
        return self._fen

    def board_to_str(self, empty: str = ".") -> str:
        """Returns a string representation of the board.

        Args:
            empty (str): A placeholder to use for empty positions.
                Must have length 1.

        Raises:
            ValueError: If `empty` does not have length 1.

        Returns:
            str: The string representation.
        """
        if len(empty) != 1:
            raise ValueError("`empty` must have length 1")
        board_str = []
        for r in range(8):
            line = []
            for bn in range(2):
                for c in range(8):
                    pos = (bn, r, c)
                    if pos not in self._board:
                        line.append(empty)
                    else:
                        piece = self._board[pos]
                        line.append(piece.fen_name)
                line.append(" ")
            board_str.append(" ".join(line))
        return "\n".join(board_str)

    def moves_to_str(
        self, columns: int = 4, captured_empty: bool = True
    ) -> str:
        """Returns a string representation of the moves for each piece.

        If `captured_empty` is True, there will be empty spaces for
        piece ids that don't have associated pieces currently on the
        board (assumed to be captured).

        Args:
            columns (int): The number of columns to split the pieces
                into. Must be positive.
            captured_empty (bool): Whether to leave empty spaces for
                captured pieces.

        Raises:
            ValueError: If `columns` is not positive.

        Returns:
            str: The string representation.
        """
        COL_PADDING = 4
        if columns <= 0:
            raise ValueError("`columns` must be positive")
        if captured_empty:
            pieces_by_id = {
                piece.id: piece for piece in self.yield_all_pieces()
            }
            all_pieces = [
                (i, pieces_by_id.get(i, None))
                for i in range(max(pieces_by_id.keys()) + 1)
            ]
        else:
            all_pieces = sorted(
                (piece.id, piece) for piece in self.yield_all_pieces()
            )
        num_rows = math.ceil(len(all_pieces) / columns)
        col_widths = [0] * columns
        col_has_piece = [False] * columns
        cols = [[] for _ in range(columns)]
        col_i = 0
        for piece_id, piece in all_pieces:
            if piece is None:
                line = f"({piece_id})"
            else:
                args = (
                    f"({piece_id})",
                    piece.name,
                    piece.pos,
                    ":",
                    " ".join(str(move.target) for move in piece.yield_moves()),
                )
                line = " ".join(map(str, args))
                col_has_piece[col_i] = True
            col = cols[col_i]
            col.append(line)
            col_widths[col_i] = max(len(line), col_widths[col_i])
            if len(col) >= num_rows:
                # start filling up the next column
                col_i += 1
        return "\n".join(
            (" " * COL_PADDING).join(
                value.ljust(width)
                for value, include_col, width in zip(
                    row, col_has_piece, col_widths
                )
                if include_col
            )
            # use zip longest because the last column may be shorter
            for row in zip_longest(*cols, fillvalue="")
        )

    def is_game_over(self) -> bool:
        """Returns whether the game is over (checkmate, stalemate, or
        draw).
        """
        return self._end_game_state is not None

    def is_in_checkmate(self) -> bool:
        """Returns whether the current player is in checkmate."""
        return self._end_game_state is EndGameState.CHECKMATE

    def winner(self) -> Optional[Color]:
        """Returns the winner of the game (for checkmate)."""
        if not self.is_in_checkmate():
            return None
        # the winner is the other color, since the current color is in
        # checkmate
        return self._current_color.other()

    def is_in_stalemate(self) -> bool:
        """Returns whether the current player is in stalemate."""
        return self._end_game_state is EndGameState.STALEMATE

    def is_kings_draw(self) -> bool:
        """Returns whether the game is a draw by only having kings."""
        return self._end_game_state is EndGameState.ONLY_KINGS_DRAW

    def is_draw(self) -> bool:
        """Returns whether the game is a draw (by the fifty move rule)."""
        return self._end_game_state is EndGameState.FIFTY_MOVE_DRAW

    def is_in_check(self) -> bool:
        """Returns whether the current player is in check."""
        return self._is_in_check

    def needs_promotion(self) -> bool:
        """Returns whether the state is waiting for a promotion for the
        last moved pawn.
        """
        return self._promoting_pawn is not None

    def promote(self, promote_type: PromoteType) -> Self:
        """Promotes the promoting pawn.

        A pawn is able to be promoted if it was last moved into the last
        row for its direction of movement.

        Args:
            promote_type (PromoteType): The type to promote to.

        Raises:
            RuntimeError: If there is no pawn waiting for a promotion.

        Returns:
            GameState: The new game state with the promoted pawn.
        """
        if not self.needs_promotion():
            raise RuntimeError("No pawn waiting for a promotion")

        if promote_type in self._promotions:
            return self._promotions[promote_type]

        pawn = self._promoting_pawn

        # create copy of board
        board = {pos: piece.copy() for pos, piece in self._board.items()}

        # replace this pawn with the specified piece type
        promoted_piece = make_promoted(pawn, promote_type)
        board[pawn.pos] = promoted_piece

        # create new game state
        new_state = self.__class__(
            _PRIVATE_game_state_constructor_key,
            white=self._white,
            black=self._black,
            current_color=self._current_color,
            # direct back to this state's previous state
            prev=self._prev,
            # use the same move from previous
            move=(self._move.pos, self._move.target),
            piece_captured=self._move.piece_captured,
            # this pawn was promoting, so there is no en passant pawn
            en_passant_pawn=None,
            half_move_clock=self._half_move_clock,
            num_moves=self._num_moves,
            board=board,
            captured=self._captured,
        )
        # cache the promotion state
        self._promotions[promote_type] = new_state
        return new_state

    def yield_all_pieces(self) -> Iterator[Piece]:
        """Yields all the pieces."""
        return iter(self._board.values())

    def yield_player_pieces(self) -> Iterator[Piece]:
        """Yields all the pieces for the current player."""
        for piece in self.yield_all_pieces():
            if piece.color is self._current_color:
                yield piece

    def yield_player_moves(self) -> Iterator[PieceMove]:
        """Yields all the possible moves for the current player."""
        for piece in self.yield_player_pieces():
            for piece_move in piece.yield_moves():
                yield piece_move

    def num_captured(self) -> int:
        """Returns the number of captured pieces."""
        return len(self._captured)

    def yield_captured(self) -> Iterator[Piece]:
        """Yields the captured pieces."""
        return iter(self._captured)

    def get_piece(self, bn: int, r: int, c: int) -> Optional[Piece]:
        """Gets the piece at the given position.

        Args:
            bn (int): The board number.
            r (int): The row.
            c (int): The column.

        Raises:
            ValueError:
                If `bn` is not 0 or 1.
                If `r` and `c` are not bounded within [0, 7].

        Returns:
            Optional[Piece]: The piece, or None.
        """
        return self._board.get((bn, r, c), None)

    def make_move(self, move: Move) -> Self:
        """Makes the given move.

        If a promotion is needed after this move, the pawn will simply
        be moved without being promoted. It is up to the caller to call
        the `GameState.promote()` method on the returned state.

        Args:
            move (Move): The move to make.

        Raises:
            RuntimeError:
                If the game is over.
                If the state is waiting for a promotion.
            ValueError: If the given move is invalid.

        Returns:
            GameState: The next game state.
        """
        move = Move.of(move)
        (bn, r, c), (tr, tc) = move

        if self.is_game_over():
            raise RuntimeError("Game is over")
        if self.needs_promotion():
            raise RuntimeError("Game needs a promotion")

        if move in self._moves:
            return self._moves[move]

        piece = self.get_piece(*move.pos)
        if piece is None:
            raise ValueError(f"No piece at position {move.pos}")
        if piece.color is not self._current_color:
            raise ValueError("Cannot move opponent's piece")
        if not piece.can_make_move(*move.capture_pos):
            raise ValueError(
                f"Piece at {move.pos} cannot move to {move.target}"
            )

        # check just in case
        other_board = self.get_piece(*move.result_pos)
        if other_board is not None:
            raise ValueError("Move squashes a piece on the other board")

        # make new copy of board
        board = {pos: piece.copy() for pos, piece in self._board.items()}
        captured = list(self._captured)

        half_move_clock = self._half_move_clock + 1

        # make move
        moved_piece = board.pop(piece.pos).move_to(move.result_pos)
        board[move.result_pos] = moved_piece

        piece_captured = board.pop(move.capture_pos, None)
        # check for en passant
        if piece.type is PieceType.PAWN:
            # reset clock: pawn moved
            half_move_clock = 0
            if c == tc:
                # going straight
                pass
            elif piece_captured is not None:
                # regular capture (diagonally)
                pass
            else:
                # change capture to en passant (same row)
                piece_captured = board.pop((bn, r, tc), None)
                if piece_captured is None:
                    raise ValueError(
                        "Pawn performed en passant, but no piece to capture"
                    )
                if piece_captured.type is not PieceType.PAWN:
                    raise ValueError("Cannot perform en passant on non-pawn")
        # capture piece
        if piece_captured is not None:
            # reset clock: piece was captured
            half_move_clock = 0
            piece_captured = piece_captured.capture()
            captured.append(piece_captured)

        # check for castle
        if piece.type is PieceType.KING:
            if not piece.has_moved and r == tr and abs(c - tc) == 2:
                # king is castling
                if tc < c:
                    if not piece.can_castle_left:
                        raise ValueError("King cannot castle")
                    # castling to the left (queenside)
                    rook_old_c = 0
                    rook_new_c = piece.left_rook_col
                else:  # tc > c
                    if not piece.can_castle_right:
                        raise ValueError("King cannot castle")
                    # castling to the right (kingside)
                    rook_old_c = 7
                    rook_new_c = piece.right_rook_col
                # move rook to new board between old and new positions
                # of king
                rook_old_pos = (bn, tr, rook_old_c)
                rook_new_pos = (1 - bn, tr, rook_new_c)
                board[rook_new_pos] = board.pop(rook_old_pos).move_to(
                    rook_new_pos
                )

        # check for en passant
        en_passant_pawn = None
        if piece.type is PieceType.PAWN and not piece.has_moved:
            if bn == 0 and abs(r - tr) == 2 and c == tc:
                # pawn advanced two steps
                en_passant_pawn = moved_piece

        num_moves = self._num_moves
        if self._current_color is Color.BLACK:
            # increments when black plays
            num_moves += 1

        # create next state
        next_state = self.__class__(
            _PRIVATE_game_state_constructor_key,
            white=self._white,
            black=self._black,
            current_color=self._current_color.other(),
            prev=self,
            move=move,
            piece_captured=piece_captured,
            en_passant_pawn=en_passant_pawn,
            half_move_clock=half_move_clock,
            num_moves=num_moves,
            board=board,
            captured=captured,
        )
        self._moves[move] = next_state
        return next_state

    def step(self) -> Self:
        """Advances a step of the game.

        Prompts the current player for a move, and also prompts them for
        promotion if necessary. Returns the next game state.

        Raises:
            RuntimeError: If the current player is a human (call
                `make_move()` instead).
            ValueError: If the move given by the player is invalid.

        Returns:
            GameState: The next game state.
        """

        player = self.current_player
        if player.is_human:
            raise RuntimeError(
                "Current player is a human (call `make_move()` instead)"
            )

        # ask player to make move
        move = player.make_move(self)
        next_state = self.make_move(move)

        if next_state.needs_promotion():
            # ask player to make promotion
            promote_type = player.promote(self)
            next_state = next_state.promote(promote_type)

        return next_state

    def run(self) -> Self:
        """Runs the game until it's over.

        Returns the last game state.
        """
        state = self
        while not state.is_game_over():
            state = state.step()
        return state

    def restart(self) -> Self:
        """Returns the starting state with the same players."""
        return self._first_state
