"""
Starts and runs a game in a window between two human players.
"""

# ======================================================================

from alicechess.game import Game
from alicechess.player import HumanPlayer

# ======================================================================


def main():
    Game(white=HumanPlayer, black=HumanPlayer).start_window()


if __name__ == "__main__":
    main()
