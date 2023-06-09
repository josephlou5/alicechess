from game_state import GameState
from player import HumanPlayer

# incorrect checkmate - fixed
fen = "rn3b1r/ppp1pp1p/8/6Q1/8/8/PPP1PPPP/R1B1KBNR/8/8/8/8/k2P4/2N5/8/3q4 b - - 8 39"

# testing
# fen = "k7/1N6/8/8/8/8/8/7K/8/8/8/8/8/8/8/8 b - - 0 0"
# fen = "k7/7R/8/8/8/8/8/1R5K/8/8/8/8/8/8/8/8 b - - 0 0"

GameState.from_fen(fen, white=HumanPlayer, black=HumanPlayer).debug()
