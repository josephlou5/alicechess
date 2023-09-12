# Changelog

## v3.0.0

- Fixed bug where castles and en passants were not registering
  - The special moves were being saved according to the position of the piece,
    but were being accessed according to the id of the piece.
- Moved castling ability logic to `GameState` rather than per-piece (#1)
  - The ability of the FEN string to exactly regenerate a board state implies
    that the castling ability for a color should be saved at the game level, not
    the piece level.
  - This change also replaced the `has_moved` property of `Piece` with the
    `is_at_start_pos()` method.

## v2.5.0

_2023-09-03 15:35_

- Cached move calculation for repeating board states
- Set required Python version to Python 3.11
  - The code uses `typing.Self`, which was introduced in Python 3.11. For type
    hint reasons, we will not remove it, and so the minimum required version
    will have to be Python 3.11.
  - Since this change broke v2.4.0, it has been yanked.

## v2.4.0 (yanked)

_2023-09-03 15:13_

- Cached move calculation for repeating board states
- Downgraded required Python version to Python 3.8 (was 3.11 before)

## v2.3.0

_2023-06-10 10:26_

- Improved debug printing for windowed games (and added ability to toggle debug)
- Added keyboard actions to the window

## v2.2.1

_2023-06-09 20:31_

- Updated readme for new command-line arguments

## v2.2.0

_2023-06-09 14:22_

- Added command-line parsing to allow launching a game between builtin players
- Added threefold repetition rule
- Tweaked castling and en passant abilities
  - According to the linked rules (should have read it thoroughly!), there were
    some potentially incorrect moves (either missing or unnecessarily present)
    that could have been generated.
- Tweaked possible move calculations: move must be valid on current board, but
  not necessarily on both boards
  - According to the linked rules (should have read it thoroughly!!!), a piece
    may teleport into a position to block check, since the move was valid on the
    board it was on (the king was not in check on that board), and the move is
    legal because the king is no longer in check.

## v2.1.0

_2023-06-09 10:43_

- Updated `of()` function to use any iterable
- Added "Pause" button for window games with no human players
- Made window buttons have the proper width for the used font

## v2.0.0

_2023-06-08 21:42_

- Removed test file (wasn't supposed to be published)
- Added `__all__` tuples to each file
- Added absolute imports (previous version wasn't even working)

## v1.0.1

_2023-06-08 21:15_

**WARNING: Does not work**

- Fixed documentation link in readme
- Added `__version__.py`

## v1.0.0

_2023-06-08 21:07_

**WARNING: Does not work**

- Initial release
