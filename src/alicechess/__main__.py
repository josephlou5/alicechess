"""
Starts and runs a game in a window between two players.
"""

# ======================================================================

import sys

from alicechess import bots
from alicechess.game import Game
from alicechess.player import HumanPlayer

# ======================================================================

PLAYERS = {"HumanPlayer": HumanPlayer}
for bot_name in bots.__all__:
    bot = getattr(bots, bot_name)
    PLAYERS[bot.__name__] = bot

_players_str = ("\n" + (" " * 4)).join(PLAYERS.keys())
USAGE_FIRST_LINE = "Usage: python -m alicechess [WHITE] [BLACK]"
USAGE = f"""\
{USAGE_FIRST_LINE}

  {__doc__.strip()}

  If no players given, will default to `HumanPlayer`.

  Accepted players:
    {_players_str}
"""

# ======================================================================


def _parse_args(args):
    if len(args) == 0:
        return HumanPlayer, HumanPlayer

    # check for help
    unknown_players = []
    for arg in args:
        if arg in ("-h", "--help"):
            print(USAGE)
            sys.exit(0)
        elif arg not in PLAYERS:
            unknown_players.append(arg)

    if len(args) != 2:
        print(USAGE_FIRST_LINE)
        if len(args) < 2:
            print("Missing black player")
        else:
            print("Too many arguments")
        sys.exit(1)

    if len(unknown_players) == 2:
        print("Unknown players:", ", ".join(unknown_players))
        sys.exit(1)
    if len(unknown_players) == 1:
        print("Unknown player:", unknown_players[0])
        sys.exit(1)

    white, black = args
    return PLAYERS[white], PLAYERS[black]


def main():
    _, *args = sys.argv
    white, black = _parse_args(args)
    Game(white=white, black=black).start_window()


if __name__ == "__main__":
    main()
