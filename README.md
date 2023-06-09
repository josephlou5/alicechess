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

- **Castling**: A king and rook may only castle if neither has moved already,
  the king is not in check, all squares between them are vacant on both boards,
  and the king does not move through check or into check. After the castle, both
  pieces will teleport to the other board.
- **En passant**: A pawn may capture another pawn through en passant if your
  pawn is on board B and the enemy pawn advances two spaces, teleporting to the
  space right next to yours on board B. (This results in a situation that looks
  like regular en passant.) Note that due to teleporting to the other board
  after each move, this can only be achieved by a pawn that _does not_ advance
  two squares on its first move.
- **Fifty move rule**: If both players have made 50 moves each where no piece
  has been captured or no pawn moved, then a player may claim a draw. However,
  to simplify this case, the game will be automatically ended with a draw
  (rather than allowing a player to claim a draw), although this is not the
  official rule. This therefore overshadows the 75-move rule, where a draw is
  automatically applied after 75 moves by both players with no captures or pawn
  movements.

## How to play

To start a game between two human players, you can easily just run the package
on the command line:

```bash
$ python -m alicechess
```

A window will come up where the game can be played.

## Playing against bots

To play a game against a bot or between bots, you must write your own script.
You should initialize a `Game` object with the appropriate players, then call
either the `start()` or `start_window()` method. To write your own bot, see the
[Writing a bot](#writing-a-bot) section.

Here is an example:

```python
"""
Plays a game between a human and a bot that plays randomly.
"""

from alicechess import Game, HumanPlayer
from alicechess.bots import RandomPlayer

if __name__ == "__main__":
    Game(white=HumanPlayer, black=RandomPlayer).start_window()
```

Note that the class names (not instances) are passed to the `Game` constructor.

The `start_window()` method will, as implied, start an interactive window where
the game can be played. However, you can also opt to use the `start()` method
instead, which will return the first `GameState` of the game, and then use
another way to ask the user for input and play the game; for instance, you could
make the game entirely textual with user input provided with the keyboard. See
the [API Documentation][docs] for more information.

In the interactive window, there is a 3 second delay for non-human player moves,
to simulate realism. This can be changed by passing a value for
`non_human_player_delay` to the `start_window()` method.

It is also possible for two bots to play against each other.

### Writing a bot

The code is factored in a way to make it very easy for you to code your own bots
to play against. Simply extend the `Player` class and implement the two abstract
methods for making a move and promoting a pawn. This class (not an instance) can
then be passed into the `Game` constructor to start a game. See the
[API Documentation][docs] for more information.

Here is an example:

```python
"""
Plays a game between a human and a bot (that I wrote).
"""

from alicechess import Game, HumanPlayer, Player, PromoteType

class Bot(Player):
    """A very good bot that I wrote."""

    def make_move(self, game_state):
        for piece in game_state.yield_player_pieces():
            for move in piece.yield_moves():
                return move

    def promote(self, game_state):
        return PromoteType.QUEEN

if __name__ == "__main__":
    Game(white=HumanPlayer, black=Bot).start_window()
```

[docs]: https://github.com/josephlou5/alicechess/blob/main/Documentation.md

## Credit

Thank you to Artyom Lisitsyn for inspiring me to pursue this project and to
Trung Phan for being my chess consultant and answering all my questions on rules
and technicalities.
