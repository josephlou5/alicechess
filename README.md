# Alice Chess

This project allows you to play Alice Chess, a variant of chess.

## Installation

The package may be installed through `pip`:

```bash
$ pip install alicechess
```

## Rules

Here is a [description of the concept and rules][rules].

[rules]: https://www.chessvariants.com/other.dir/alice.html

Notable game rules:

- A piece's move must be valid on the board it is on, which means that a piece
  on Board B can block a check on Board A after teleporting (since the move was
  valid on Board B, and the move overall was legal because the king is not
  staying in check). See the above link for a more detailed argument on this.
- **Castling**: A king and rook may only castle if neither has moved already,
  the king is not in check, the squares they will move to are vacant on both
  boards, and the king does not move through check (on Board A) or into check.
  After the castle, both pieces will teleport to the other board.
- **En passant**: A pawn may capture another pawn through en passant if your
  pawn is on Board B and the enemy pawn advances two spaces, teleporting to the
  space right next to yours on Board B. (This results in a situation that looks
  like regular en passant.) Note that due to teleporting to the other board
  after each move, this can only be achieved by a pawn that _does not_ advance
  two squares on its first move. Also, if there is a piece on Board B where the
  en passant move would go (i.e., your pawn can already capture a piece
  normally), then en passant will not take place.
- **Fifty move rule**: If both players have made 50 moves each where no piece
  has been captured or no pawn moved, then a player may claim a draw. However,
  to simplify this case, the game will be automatically ended with a draw
  (rather than allowing a player to claim a draw). This therefore overshadows
  the 75-move rule, where a draw is automatically applied after 75 moves by both
  players with no captures or pawn movements.
- **Threefold repetition rule**: If a board position appears three times in a
  game (not necessarily in a row), then a player may claim a draw. However, to
  simplify this case, the game will be automatically ended with a draw (rather
  than allowing a player to claim a draw).

## How to play

### Command Line

To start a game between two human players, you can run the package on the
command line:

```bash
$ python -m alicechess
```

A window will come up where the game can be played.

You can also change the players you want to play with by specifying any two of
the builtin players (`HumanPlayer` or any of the bots defined in `bots.py`):

```bash
$ python -m alicechess HumanPlayer RandomPlayer
```

See `python -m alicechess --help` for a list of the possible players.

### Script

You can also use a script to run a game. You must initialize a `Game` object
with the appropriate players, then call the `start_window()` or `start()`
method.

Here is an example:

```python
from alicechess import Game, HumanPlayer
from alicechess.bots import RandomPlayer

if __name__ == "__main__":
    Game(white=HumanPlayer, black=RandomPlayer).start_window()
```

Note that the class names (not instances) are passed to the `Game` constructor.

The `start_window()` method will, as implied, start an interactive window where
the game can be played. However, you can also opt to use the `start()` method
instead, which will return the first `GameState` of the game, and then use
another way to ask the user(s) for input and play the game; for instance, you
could make the game entirely textual with user input provided with the keyboard.
See the [API Documentation][docs] for more information on `GameState` objects,
and check out [`window.py`][] for how the windowed game is handled.

In the interactive window, there is a 3 second delay for non-human player moves,
to simulate realism. This can be changed by passing a value for
`non_human_player_delay` to the `start_window()` method.

To play against your own bot, see the [Writing a bot](#writing-a-bot) section.

It is also possible for two bots to play against each other.

### Writing a bot

The code is factored in a way to make it very easy for you to code your own bots
to play against. Simply extend the `Player` class and implement the two abstract
methods for making a move and promoting a pawn. This class (not an instance) can
then be passed into the `Game` constructor to start a game. See the
[API Documentation][docs] for more information.

Here is an example:

```python
from alicechess import Game, HumanPlayer, Player, PromoteType

class MyBot(Player):
    """A very good bot that I wrote."""

    def make_move(self, game_state):
        for piece in game_state.yield_player_pieces():
            for move in piece.yield_moves():
                return move

    def promote(self, game_state):
        return PromoteType.QUEEN

if __name__ == "__main__":
    Game(white=HumanPlayer, black=MyBot).start_window()
```

## Credit

Thank you to Artyom Lisitsyn for inspiring me to pursue this project and to
Trung Phan for being my chess consultant and answering all my questions on rules
and technicalities.

[docs]: https://github.com/josephlou5/alicechess/blob/main/Documentation.md
[`window.py`]: https://github.com/josephlou5/alicechess/blob/main/src/alicechess/window.py
