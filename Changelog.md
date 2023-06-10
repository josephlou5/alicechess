# Changelog

## v2.3.0

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
