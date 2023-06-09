# Changelog

## v2.2.0

- Added command-line parsing to allow launching a game between builtin players
- Added threefold repetition rule
- Tweaked castling and en passant abilities
  - According to the linked rules (should have read it thoroughly!), there were
    some potentially incorrect moves (either missing or unnecessarily present)
    that could have been generated.

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
