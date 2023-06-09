"""
Example random bots.
"""

# =============================================================================

import random
from typing import Dict

from alicechess.game_state import GameState
from alicechess.player import Player
from alicechess.position import Move
from alicechess.utils import PieceType, PromoteType

# =============================================================================

__all__ = (
    "RandomPlayer",
    "PrioritizedRandomPlayer",
)

# =============================================================================


class RandomPlayer(Player):
    """A bot that picks a random move to make."""

    def make_move(self, game_state: GameState) -> Move:
        return random.choice(list(game_state.yield_player_moves()))

    def promote(self, game_state: GameState) -> PromoteType:
        return PromoteType.by_index(random.randrange(len(PromoteType)))


class PrioritizedRandomPlayer(Player):
    """A bot that picks a random move to make, prioritizing moves that
    put the other king in checkmate or check, then prioritizing moves
    that capture an enemy piece. Out of those priorities, it tries to
    not put the moved piece in a threatened position, and also tries to
    capture more valuable pieces.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # maps: int -> promote type
        self._saved_promotions: Dict[int, PromoteType] = {}

    def make_move(self, game_state: GameState) -> Move:
        PIECE_VALUES = {
            PieceType.KING: 0,
            PieceType.QUEEN: 8,
            PieceType.ROOK: 5,
            PieceType.KNIGHT: 3,
            PieceType.BISHOP: 3,
            PieceType.PAWN: 1,
        }

        max_weight = None
        max_weight_moves = []
        for move in game_state.yield_player_moves():
            next_state = game_state.make_move(move)
            if next_state.needs_promotion():
                # try every promotion
                check_states = []
                for promote_type in PromoteType:
                    state = next_state.promote(promote_type)
                    check_states.append(state)
                    self._saved_promotions[state.id] = promote_type
            else:
                check_states = [next_state]

            for state in check_states:
                move_made = state.move
                is_threatened = move_made.piece_moved.is_threatened

                priority = 0
                if state.is_in_checkmate():
                    priority = 3
                elif state.is_in_check():
                    priority = 2
                elif move_made.move_captured:
                    priority = 1

                # not capturing a piece has value 0
                value = 0
                if move_made.move_captured:
                    value = PIECE_VALUES[move_made.piece_captured.type]

                weight = (priority, 0 if is_threatened else 1, value)
                if max_weight is None or weight > max_weight:
                    max_weight = weight
                    max_weight_moves = [move]
                elif weight == max_weight:
                    max_weight_moves.append(move)

        return random.choice(max_weight_moves)

    def promote(self, game_state: GameState) -> PromoteType:
        promote_type = self._saved_promotions.get(game_state.id, None)
        if promote_type is not None:
            return promote_type
        return PromoteType.by_index(random.randrange(len(PromoteType)))
