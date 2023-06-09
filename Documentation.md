# Alice Chess API Documentation

## `Player`

Represents a player.

**Properties**

| Name       | Type        | Description                   |
| ---------- | ----------- | ----------------------------- |
| `color`    | [`Color`][] | The player color.             |
| `is_human` | `bool`      | Whether this player is human. |

**Abstract Methods**

- `make_move(game_state: GameState) -> Move`

  Called when this player should make their next move.

  _Arguments:_

  | Name         | Type            | Description             |
  | ------------ | --------------- | ----------------------- |
  | `game_state` | [`GameState`][] | The current game state. |

  _Returns_ [`Move`][]: The move to make.

- `promote(game_state: GameState) -> PromoteType`

  Called when this player can promote a pawn.

  _Arguments:_

  | Name         | Type            | Description             |
  | ------------ | --------------- | ----------------------- |
  | `game_state` | [`GameState`][] | The current game state. |

  _Returns_ [`PromoteType`][]: The piece type to promote to.

**Examples**

See [`bots.py`](bots.py) for some example simple bots.

## `Game`

Represents a game of Alice Chess.

Wrapper around [`GameState`][] to easily start a game.

**Constructors**

- `Game(*, white: Type[Player], black: Type[Player])`

  Initializes a Game with the given players.

  The players must be subclasses of [`Player`][] (not instances).

  _Arguments:_

  | Name    | Type                   | Description           |
  | ------- | ---------------------- | --------------------- |
  | `white` | `Type[`[`Player`][]`]` | The player for white. |
  | `black` | `Type[`[`Player`][]`]` | The player for black. |

**Methods**

- `new() -> GameState`

  Returns a new game.

  _Returns_ [`GameState`][]: The first state of the game.

**Example**

```python
from alicechess import Game, HumanPlayer

game = Game(white=HumanPlayer, black=SuperGoodBotPlayer)
game.start().run()
```

## `WindowGame`

_Subclass of [`Game`][]._

Represents a game of Alice Chess in a visual window.

**Methods**

- `start_window(**kwargs)`

  Starts the game in a window.

  Any keyword arguments will be passed to the [`Window`][] constructor.

## `GameState`

A `GameState` is an immutable state of a game. It includes the board state, the
previous move and previous `GameState`, the captured pieces, the possible moves,
the end game state, and more.

**Constructors**

- `GameState.new(*, white: Type[Player], black: Type[Player])`

  Initializes the first GameState of a game.

- `GameState.from_fen(fen: str, *, white: Type[Player], black: Type[Player])`

  Initializes a GameState from a FEN string, using the given players.

**Properties**

| Name              | Type                           | Description                                                             |
| ----------------- | ------------------------------ | ----------------------------------------------------------------------- |
| `id`              | `int`                          | The game state id.                                                      |
| `white`           | [`Player`][]                   | The white player.                                                       |
| `black`           | [`Player`][]                   | The black player.                                                       |
| `prev`            | `Optional[GameState]`          | The previous `GameState`.                                               |
| `move`            | `Optional[`[`PieceMoved`][]`]` | The move from the previous `GameState`.                                 |
| `current_color`   | [`Color`][]                    | The color of the current player.                                        |
| `current_player`  | [`Player`][]                   | The current player.                                                     |
| `half_move_clock` | `int`                          | The number of half-moves since the last capture or the last pawn moved. |
| `num_moves`       | `int`                          | The number of full moves played in the entire game.                     |

**Methods**

- `fen() -> str`

  Returns the FEN representation of the game.

  Since Alice Chess has two boards, the piece placement portion is doubled in
  length, where the first 8 ranks refer to Board A (on the left) and the last 8
  ranks refer to Board B (on the right).

- `board_to_str(empty: str = " .") -> str`

  Returns a string representation of the board.

  _Arguments:_

  | Name    | Type  | Description                                                   |
  | ------- | ----- | ------------------------------------------------------------- |
  | `empty` | `str` | A placeholder to use for empty positions. Must have length 2. |

  _Raises:_

  - `ValueError`: If `empty` does not have length 2.

  _Returns_ `str`: The string representation.

- `moves_to_str(columns: int = 4, captured_empty: bool = True) -> str`

  Returns a string representation of the moves for each piece.

  If `captured_empty` is `True`, there will be empty spaces for piece ids that
  don't have associated pieces currently on the board (assumed to be captured).

  _Arguments:_

  | Name             | Type   | Description                                                       |
  | ---------------- | ------ | ----------------------------------------------------------------- |
  | `columns`        | `int`  | The number of columns to split the pieces into. Must be positive. |
  | `captured_empty` | `bool` | Whether to leave empty spaces for captured pieces.                |

  _Raises:_

  - `ValueError`: If `columns` is not positive.

  _Returns_ `str`: The string representation.

- `is_game_over() -> bool`

  Returns whether the game is over (checkmate, stalemate, or draw).

- `is_in_checkmate() -> bool`

  Returns whether the current player is in checkmate.

- `winner() -> Optional[Color]`

  Returns the winner of the game (for checkmate).

- `is_in_stalemate() -> bool`

  Returns whether the current player is in stalemate.

- `is_kings_draw() -> bool`

  Returns whether the game is a draw by only having kings.

- `is_draw() -> bool`

  Returns whether the game is a draw (by the fifty move rule).

- `is_in_check() -> bool`

  Returns whether the current player is in check.

- `needs_promotion() -> bool`

  Returns whether the state is waiting for a promotion for the last moved pawn.

- `promote(promote_type: PromoteType) -> GameState`

  Promotes the promoting pawn.

  A pawn is able to be promoted if it was last moved into the last row for its
  direction of movement.

  _Arguments:_

  | Name           | Type              | Description             |
  | -------------- | ----------------- | ----------------------- |
  | `promote_type` | [`PromoteType`][] | The type to promote to. |

  _Raises:_

  - `RuntimeError`: If there is no pawn waiting for a promotion.

  _Returns_ `GameState`: The new game state with the promoted pawn.

- `yield_all_pieces() -> Iterator[Piece]`

  Yields all the pieces.

- `yield_player_pieces() -> Iterator[Piece]`

  Yields all the pieces for the current player.

- `yield_player_moves() -> Iterator[PieceMove]`

  Yields all the possible moves for the current player.

- `yield_captured() -> Iterator[Piece]`

  Yields the captured pieces.

- `get_piece(bn: int, r: int, c: int) -> Optional[Piece]`

  Gets the piece at the given position.

  _Arguments:_

  | Name | Type  | Description       |
  | ---- | ----- | ----------------- |
  | `bn` | `int` | The board number. |
  | `r`  | `int` | The row.          |
  | `c`  | `int` | The column.       |

  _Raises:_

  - `ValueError`:
    - If `bn` is not 0 or 1.
    - If `r` and `c` are not bounded within [0, 7].

  _Returns_ `Optional[`[`Piece`][]`]`: The piece, or `None`.

- `make_move(move: Move) -> GameState`

  Makes the given move.

  If a promotion is needed after this move, the pawn will simply be moved
  without being promoted. It is up to the caller to call the
  `GameState.promote()` method on the returned state.

  _Arguments:_

  | Name   | Type       | Description       |
  | ------ | ---------- | ----------------- |
  | `move` | [`Move`][] | The move to make. |

  _Raises:_

  - `RuntimeError`:
    - If the game is over.
    - If the state is waiting for a promotion.
  - `ValueError`: If the given move is invalid.

  _Returns_ `GameState`: The next game state.

- `step() -> GameState`

  Advances a step of the game.

  Prompts the current player for a move, and also prompts them for promotion if
  necessary. Returns the next game state.

  _Raises:_

  - `RuntimeError`: If the current player is a human (call `make_move()`
    instead).
  - `ValueError`: If the move given by the player is invalid.

  _Returns_ `GameState`: The next game state.

- `run() -> GameState`

  Runs the game until it's over.

  Returns the last game state.

- `restart() -> GameState`

  Returns the starting state with the same players.

## `Piece`

Represents a piece.

Two special pieces, [`King`][] and [`Pawn`][], are described below.

**Properties**

| Name            | Type                | Description                                                                        |
| --------------- | ------------------- | ---------------------------------------------------------------------------------- |
| `id`            | `int`               | The piece id.                                                                      |
| `name`          | `str`               | The piece name.                                                                    |
| `type`          | [`PieceType`][]     | The piece type.                                                                    |
| `color`         | [`Color`][]         | The piece color.                                                                   |
| `has_moved`     | `bool`              | Whether this piece has moved.                                                      |
| `pos`           | [`BoardPosition`][] | The piece position.                                                                |
| `num_moves`     | `int`               | The number of possible moves.                                                      |
| `is_captured`   | `bool`              | Whether this piece is captured.                                                    |
| `is_threatened` | `bool`              | Whether this piece is being threatened on the current board. `False` if not known. |

**Methods**

- `copy() -> Piece`

  Returns a copy of this piece.

  _Returns_ [`Piece`][]: The copy.

- `yield_moves() -> Iterator[PieceMove]`

  Yields the possible moves for this piece.

  _Yields_ [`PieceMove`][]: Each possible move.

- `can_make_move(bn: int, tr: int, tc: int) -> bool`

  Returns whether this piece can move to the given position.

  _Arguments:_

  | Name | Type  | Description        |
  | ---- | ----- | ------------------ |
  | `bn` | `int` | The board number.  |
  | `tr` | `int` | The target row.    |
  | `tc` | `int` | The target column. |

  _Raises:_

  - `ValueError`:
    - If `bn` is not 0 or 1.
    - If `tr` and `tc` are not bounded within [0, 7].

  _Returns_ `bool`: Whether this piece can move to the given position.

- `move_to(pos: BoardPosition) -> Piece`

  Returns a copy of this piece that is moved to the given position.

  Also changes `has_moved` to `True`.

  _Arguments:_

  | Name  | Type                | Description              |
  | ----- | ------------------- | ------------------------ |
  | `pos` | [`BoardPosition`][] | The position to move to. |

  _Returns_ [`Piece`][]: The copy.

- `capture() -> Piece`

  Returns a copy of this piece that is captured.

  _Returns_ [`Piece`][]: The copy.

### `King`

_Subclass of [`Piece`][]._

**Additional Properties**

| Name               | Type            | Description                                                           |
| ------------------ | --------------- | --------------------------------------------------------------------- |
| `can_castle_left`  | `bool`          | Whether the king can castle to the left (queenside).                  |
| `left_rook_col`    | `Optional[int]` | The column the left rook castles to, if the king can castle with it.  |
| `can_castle_right` | `bool`          | Whether the king can castle to the right (kingside).                  |
| `right_rook_col`   | `Optional[int]` | The column the right rook castles to, if the king can castle with it. |

### `Pawn`

_Subclass of [`Piece`][]._

**Additional Properties**

| Name          | Type   | Description                       |
| ------------- | ------ | --------------------------------- |
| `dr`          | `int`  | The direction of movement.        |
| `can_promote` | `bool` | Whether the pawn can be promoted. |

## Utilities

### `Color`

Enum for the possible colors for each piece.

**Values**

- `Color.WHITE`
- `Color.BLACK`

**Methods**

- `abbr() -> str`

  Returns the first letter of the color.

- `title() -> str`

  Returns the enum name as a title string (first letter is capital; all others
  are lowercase).

- `other() -> Color`

  Returns the other color.

### Positions

Positions are represented as tuples of row and column `(r, c)` or as tuples of
board number, row, and column `(bn, r, c)`. The following sections describe the
actual objects [`Position`][] and [`BoardPosition`][] that are used throughout
the code, but any methods that expect a `Position` or `BoardPosition` can also
accept tuples representing the same.

#### `Position`

Represents a position on a single board.

**Constructors**

- `Position(r: int, c: int)`

  Initializes a Position.

- `Position.of(obj)`

  Initializes a Position from a tuple or `Position` object.

- `Position.from_code(code: str)`

  Constructs a Position based on its code.

**Properties**

| Name   | Type              | Description                                |
| ------ | ----------------- | ------------------------------------------ |
| `pos`  | `Tuple[int, int]` | The row and column.                        |
| `r`    | `int`             | The row.                                   |
| `c`    | `int`             | The column.                                |
| `code` | `str`             | The position code (in algebraic notation). |

**Static Methods**

- `to_str(iterable: Iterable[Position], sep: str = " ") -> str`

  Returns the `Position`s in the given iterable as a string.

#### `BoardPosition`

Represents a position on either board.

**Constructors**

- `BoardPosition(r: int, c: int)`

  Initializes a BoardPosition.

- `BoardPosition.of(obj)`

  Initializes a BoardPosition from a tuple or `BoardPosition` object.

- `BoardPosition.from_code(code: str)`

  Constructs a BoardPosition based on its code.

**Properties**

| Name   | Type                   | Description                                |
| ------ | ---------------------- | ------------------------------------------ |
| `pos`  | `Tuple[int, int, int]` | The board number, row, and column.         |
| `bn`   | `int`                  | The board number.                          |
| `r`    | `int`                  | The row.                                   |
| `c`    | `int`                  | The column.                                |
| `code` | `str`                  | The position code (in algebraic notation). |

**Static Methods**

- `to_str(iterable: Iterable[BoardPosition], sep: str = " ") -> str`

  Returns the `BoardPosition`s in the given iterable as a string.

### Moves

Moves are represented as tuples of a piece's [`BoardPosition`][] and its target
resulting [`Position`][] `((bn, r, c), (tr, tc))`. The following sections
describe the actual objects `Move`, `PieceMove`, and `PieceMoved` that are used
throughout the code, but any methods that expect a `Move` can also accept a
tuple representing the same. (`PieceMove` and `PieceMoved` objects are only ever
returned or accessed by the user.)

#### `Move`

Represents a move of a piece.

**Constructors**

- `Move(pos: BoardPosition, target: Position)`

  Initializes a Move.

- `Move.of(obj)`

  Initializes a Move from a tuple or `Move` object.

**Properties**

| Name          | Type                | Description                                        |
| ------------- | ------------------- | -------------------------------------------------- |
| `pos`         | [`BoardPosition`][] | The piece position.                                |
| `target`      | [`Position`][]      | The target position.                               |
| `capture_pos` | [`BoardPosition`][] | The capture position.                              |
| `result_pos`  | [`BoardPosition`][] | The piece's resulting position, after teleporting. |

**Static Methods**

- `to_str(iterable: Iterable[Move], sep: str = " ") -> str`

  Returns the `Move`s in the given iterable as a string.

#### `PieceMove`

Represents a possible move for a piece, which is a [`Move`][] that includes
information about the piece.

**Constructors**

- `PieceMove(pos: BoardPosition, target: Position, piece: Piece)`

  Initializes a PieceMove.

- `PieceMove.of(obj)`

  Initializes a PieceMove from a tuple or `PieceMove` object.

**Properties**

| Name          | Type                | Description                                        |
| ------------- | ------------------- | -------------------------------------------------- |
| `pos`         | [`BoardPosition`][] | The piece position.                                |
| `target`      | [`Position`][]      | The target position.                               |
| `capture_pos` | [`BoardPosition`][] | The capture position.                              |
| `result_pos`  | [`BoardPosition`][] | The piece's resulting position, after teleporting. |
| `piece_moved` | [`Piece`][]         | The piece that is being moved.                     |

**Static Methods**

- `to_str(iterable: Iterable[PieceMove], sep: str = " ") -> str`

  Returns the `PieceMove`s in the given iterable as a string.

#### `PieceMoved`

Represents a move done by a piece, which is a [`PieceMove`][] that includes
information about a possible capture.

These are constructed by [`GameState`][] objects when moves are made, and users
will likely not need to create them themselves.

**Constructors**

- `PieceMoved(pos: BoardPosition, target: Position, piece: Piece, captured: Optional[Piece] = None)`

  Initializes a PieceMoved.

- `PieceMoved.of(obj)`

  Initializes a PieceMoved from a tuple or `PieceMoved` object.

**Properties**

| Name             | Type                      | Description                                        |
| ---------------- | ------------------------- | -------------------------------------------------- |
| `pos`            | [`BoardPosition`][]       | The piece position.                                |
| `target`         | [`Position`][]            | The target position.                               |
| `capture_pos`    | [`BoardPosition`][]       | The capture position.                              |
| `result_pos`     | [`BoardPosition`][]       | The piece's resulting position, after teleporting. |
| `piece_moved`    | [`Piece`][]               | The piece that was moved.                          |
| `move_captured`  | `bool`                    | Whether the move captured a piece.                 |
| `piece_captured` | `Optional[`[`Piece`][]`]` | The piece that was captured, if given.             |

**Static Methods**

- `to_str(iterable: Iterable[PieceMoved], sep: str = " ") -> str`

  Returns the `PieceMoved`s in the given iterable as a string.

### `PieceType`

Enum for the possible piece types.

**Values**

- `PieceType.KING`
- `PieceType.QUEEN`
- `PieceType.ROOK`
- `PieceType.KNIGHT`
- `PieceType.BISHOP`
- `PieceType.PAWN`

**Methods**

- `title() -> str`

  Returns the enum name as a title string (first letter is capital; all others
  are lowercase).

### `PromoteType`

Enum for the possible promotion types.

**Values**

- `PromoteType.QUEEN`
- `PromoteType.ROOK`
- `PromoteType.KNIGHT`
- `PromoteType.BISHOP`

**Static Methods**

- `by_index(i) -> PromoteType`

  Returns the `PromoteType` at index `i` (in the order above).

## Others

### `MovesCalculator`

This is a helper class to calculate the possible moves for a given board state.
There was a lot of code involved (such as checking for special cases like
castling and en passant), including additional helper methods, so it was cleaner
to bring it out to another class instead of including all of it in the
`GameState` constructor. However, this means that only a `MovesCalculator` needs
to know the possible ways a piece can move, and individual [`Piece`][] objects
are simply given their possible moves.

### `EndGameState`

Enum for the possible states for the end of the game.

**Values**

- `EndGameState.CHECKMATE`
- `EndGameState.STALEMATE`
- `EndGameState.ONLY_KINGS_DRAW`: A draw by only having kings left on the board.
- `EndGameState.FIFTY_MOVE_DRAW`: A draw through the fifty move rule.

### `HumanPlayer`

A `HumanPlayer` is a [`Player`][] that does not implement the `make_move()` and
`promote()` methods, and instead relies on other means of input to make moves in
the game. For instance, `HumanPlayer`s in a [`WindowGame`][] will use click
events to select pieces and move them.

You will only need to use this if you want a human to play in a game by passing
`HumanPlayer` as the `white` or `black` player to a [`Game`][] or
[`WindowGame`][].

### `Window`

A `Window` is where a game can be played visually.

It uses the [`tkinter`][] library to create the window. In my experience I have
only ever used the [`Canvas`][] object, so that is what I also used here. I
believe there is more that `tkinter` has to offer, but I have stuck with what I
know. The package comes installed with Python and is available on most Unix and
Windows systems.

**Constructors**

- `Window(game_state: GameState, title: str = "Alice Chess", non_human_player_delay: int = 3)`

  Initializes a Window.

  _Arguments:_

  | Name                     | Type            | Description                                                               |
  | ------------------------ | --------------- | ------------------------------------------------------------------------- |
  | `game_state`             | [`GameState`][] | The starting game state.                                                  |
  | `title`                  | `str`           | The title of the window.                                                  |
  | `non_human_player_delay` | `int`           | The number of seconds of delay for non-human players to simulate realism. |

**Methods**

- `run()`

  Runs the game.

<!-- External reference links -->

[`tkinter`]: https://docs.python.org/3/library/tkinter.html
[`Canvas`]: https://tkdocs.com/tutorial/canvas.html

<!-- API reference links -->

[`BoardPosition`]: #boardposition
[`Color`]: #color
[`EndGameState`]: #endgamestate
[`Game`]: #game
[`GameState`]: #gamestate
[`HumanPlayer`]: #humanplayer
[`King`]: #king
[`Move`]: #move
[`MovesCalculator`]: #movescalculator
[`Pawn`]: #pawn
[`Piece`]: #piece
[`PieceMove`]: #piecemove
[`PieceMoved`]: #piecemoved
[`PieceType`]: #piecetype
[`Player`]: #player
[`Position`]: #position
[`PromoteType`]: #promotetype
[`Window`]: #window
[`WindowGame`]: #windowgame
