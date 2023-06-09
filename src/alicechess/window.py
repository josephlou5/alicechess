"""
Window class.
"""

# =============================================================================

import math
import tkinter as _tk
import tkinter.font as _TkFont
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from PIL import Image, ImageTk
except ImportError as ex:
    raise RuntimeError(
        """\
Pillow must be installed to run a game in a window:

  $ python -m pip install Pillow
"""
    ) from ex

from alicechess.game_state import GameState
from alicechess.pieces import Piece
from alicechess.position import BoardPosition, Position
from alicechess.utils import Color, PieceType, PromoteType, check_brc_bool

# =============================================================================

__all__ = ("Window",)

# =============================================================================

# The size of a square cell.
SQUARE_SIZE = 70
HALF_SQUARE_SIZE = SQUARE_SIZE / 2
# The padding between the two boards.
BOARD_PADDING = 50
# The offset from the edges of the board to a label.
LABEL_OFFSET = HALF_SQUARE_SIZE
# The offset to the top-left corner of Board A.
X_OFFSET = 70
Y_OFFSET = 70
# The offset to the left side of Board B.
X_OFFSET2 = X_OFFSET + SQUARE_SIZE * 8 + BOARD_PADDING
# The offset from the bottom of the board to the bottom of the screen.
Y_OFFSET_BOT = 180

# Calculated dimensions of the entire window.
WIDTH = X_OFFSET + SQUARE_SIZE * 8 + BOARD_PADDING + SQUARE_SIZE * 8 + X_OFFSET
HALF_WIDTH = WIDTH / 2
HEIGHT = Y_OFFSET + SQUARE_SIZE * 8 + Y_OFFSET_BOT

BUTTON_PADDING = 5

POSSIBLE_DOT_RADIUS = 5

# Board colors
WHITE_COLOR = "white"
BLACK_COLOR = "gray"
SELECT_COLOR = "green"
POSSIBLE_COLOR = "blue"
LAST_MOVE_COLOR = "#" + "".join(f"{x:02x}" for x in (102, 255, 178))

# The fonts to use.
FONTS = ("SF Pro",)

# Images
PICTURE_FOLDER = Path(__file__).parent / "pictures"
PICTURE_EXT = ".png"

# =============================================================================


def _button_width(font: _TkFont.Font, text: str) -> int:
    return BUTTON_PADDING + font.measure(text) + BUTTON_PADDING


def _button_middle(coords) -> Tuple[float, float]:
    x1, y1, x2, y2 = coords
    return (x1 + x2) / 2, (y1 + y2) / 2


# =============================================================================


def _black_on_button(game_state: GameState) -> bool:
    # black should only be on the bottom if white is not a human but
    # black is a human
    # otherwise, default to white on bottom
    return not game_state.white.is_human and game_state.black.is_human


def _brc_to_xy(
    game_state: GameState, pos: BoardPosition, *, center: bool
) -> Tuple[int, int]:
    """Calculates the xy-coordinates of the top-left or center of the
    square for the given board position.
    """
    bn, r, c = pos
    if _black_on_button(game_state):
        # flip the coordinates
        r = 7 - r
        c = 7 - c
    x = (X_OFFSET, X_OFFSET2)[bn] + SQUARE_SIZE * c
    y = Y_OFFSET + SQUARE_SIZE * r
    if center:
        x += HALF_SQUARE_SIZE
        y += HALF_SQUARE_SIZE
    return x, y


def _xy_to_brc(
    game_state: GameState, x: int, y: int
) -> Optional[BoardPosition]:
    """Calculates the board position of the given xy-coordinates."""
    bn = 0
    # int truncates (toward 0), so must use `math.floor()` to account
    # for possible negative numbers
    r = math.floor((y - Y_OFFSET) / SQUARE_SIZE)
    c = math.floor((x - X_OFFSET) / SQUARE_SIZE)
    if c >= 8:  # try other board
        bn = 1
        c = math.floor((x - X_OFFSET2) / SQUARE_SIZE)
    if _black_on_button(game_state):
        # flip the coordinates
        r = 7 - r
        c = 7 - c
    if not check_brc_bool(bn, r, c):
        # invalid coords (not within boards)
        return None
    return BoardPosition(bn, r, c)


def _within_coords(coords, x, y):
    x1, y1, x2, y2 = coords
    return x1 <= x <= x2 and y1 <= y <= y2


# =============================================================================


class Square:
    """Represents a square cell on the board.

    Methods:
        reset(): Resets this square.
        select(): Selects this square.
        last_move(): Highlights this square as the last move.
        possible(): Sets this square as a possible move.
    """

    def __init__(
        self,
        game_state: GameState,
        canvas: _tk.Canvas,
        bn: int,
        r: int,
        c: int,
    ):
        self._canvas = canvas
        self._color = WHITE_COLOR if (r + c) % 2 == 0 else BLACK_COLOR

        x, y = _brc_to_xy(game_state, (bn, r, c), center=False)
        self._square = canvas.create_rectangle(
            x, y, x + SQUARE_SIZE, y + SQUARE_SIZE, fill=self._color
        )
        x_mid = x + HALF_SQUARE_SIZE
        y_mid = y + HALF_SQUARE_SIZE
        self._dot = canvas.create_oval(
            x_mid - POSSIBLE_DOT_RADIUS,
            y_mid - POSSIBLE_DOT_RADIUS,
            x_mid + POSSIBLE_DOT_RADIUS,
            y_mid + POSSIBLE_DOT_RADIUS,
            fill=POSSIBLE_COLOR,
            tags=("possible_dot",),
            state="hidden",
        )

    def _set_color(self, color: str):
        self._canvas.itemconfig(self._square, fill=color)

    def reset(self):
        """Resets this square."""
        self._set_color(self._color)
        self.reset_possible()

    def select(self):
        """Selects this square."""
        self._set_color(SELECT_COLOR)

    def last_move(self):
        """Highlights this square as the last move."""
        self._set_color(LAST_MOVE_COLOR)

    def possible(self):
        """Sets this square as a possible move."""
        self._canvas.itemconfig(self._dot, state="normal")

    def reset_possible(self):
        """Hides this square's possible move dot."""
        self._canvas.itemconfig(self._dot, state="hidden")


class Window:
    """A window where the game is played.

    Methods:
        run(): Runs the game.
    """

    def __init__(
        self,
        game_state: GameState,
        title: str = "Alice Chess",
        non_human_player_delay: int = 3,
    ):
        """Initializes a Window.

        Args:
            game_state (GameState): The starting game state.
            title (str): The title of the window.
            non_human_player_delay (int): The number of seconds of delay
                for non-human players to simulate realism.

        Raises:
            ValueError:
                If `non_human_player_delay` is negative.
            FileNotFoundError:
                If the pictures folder does not exist.
                If a piece image file is not found.
        """
        if not PICTURE_FOLDER.exists():
            raise FileNotFoundError(
                f"Pictures folder does not exist: {PICTURE_FOLDER}"
            )

        if non_human_player_delay < 0:
            raise ValueError("`non_human_player_delay` cannot be negative")
        self._delay = non_human_player_delay * 1000

        self._game = game_state
        white = game_state.white
        black = game_state.black
        self._has_human_player = white.is_human or black.is_human
        self._undo_state = None
        self._find_undo_state()

        if _black_on_button(game_state):

            def label(i):
                num = str(8 - i)
                letter = "abcdefgh"[7 - i]
                return num, letter

        else:

            def label(i):
                num = str(i + 1)
                letter = "abcdefgh"[i]
                return num, letter

        self._tk = _tk.Tk()
        self._tk.title(title)

        # find font to use
        self._font = None
        families = set(_TkFont.families())
        for font in FONTS:
            if font in families:
                self._font = font
                break
        font30 = (self._font, 30)
        font20 = (self._font, 20)
        self._font15 = _TkFont.Font(self._tk, (self._font, 15))

        self._canvas = canvas = _tk.Canvas(
            self._tk, width=WIDTH, height=HEIGHT
        )
        canvas.pack()

        # title
        canvas.create_text(HALF_WIDTH, Y_OFFSET / 2, text=title, font=font30)

        # piece images
        # 5:4 scale for image:square sizes
        img_size = (int(SQUARE_SIZE * 5 / 4),) * 2
        # maps: color -> piece type -> image object
        self._images: Dict[Color, Dict[PieceType, ImageTk.PhotoImage]] = {}
        for color in Color:
            color_images = {}
            for piece_type in PieceType:
                image_path = (
                    PICTURE_FOLDER
                    / f"{color.abbr()}{piece_type.value}{PICTURE_EXT}"
                )
                if not image_path.exists():
                    raise FileNotFoundError(
                        f"Piece image file not found: {image_path}"
                    )
                img = Image.open(image_path)
                img = img.resize(img_size, Image.ANTIALIAS)
                color_images[piece_type] = ImageTk.PhotoImage(img)
            self._images[color] = color_images

        # maps: piece id -> image id
        self._piece_images: Dict[int, int] = {}

        # draw boards
        self._squares: Dict[BoardPosition, Square] = {}
        for bn in range(2):
            for r in range(8):
                for c in range(8):
                    self._squares[bn, r, c] = Square(
                        game_state, canvas, bn, r, c
                    )

        # labels
        board1_x = X_OFFSET - LABEL_OFFSET
        board2_x = X_OFFSET2 + LABEL_OFFSET
        board2_end_x = WIDTH - X_OFFSET + LABEL_OFFSET
        under_y = HEIGHT - Y_OFFSET_BOT + LABEL_OFFSET
        for i in range(8):
            num, letter = label(i)
            # row labels (numbers)
            y = under_y - SQUARE_SIZE * (i + 1)
            canvas.create_text(board1_x, y, text=num, font=font20)
            canvas.create_text(board2_end_x, y, text=num, font=font20)
            # column labels (letters)
            x1 = board1_x + SQUARE_SIZE * (i + 1)
            x2 = board2_x + SQUARE_SIZE * i
            canvas.create_text(x1, under_y, text=letter, font=font20)
            canvas.create_text(x2, under_y, text=letter, font=font20)

        # between the center of the label text and the bottom of the
        # window
        bottom_y = HEIGHT - (Y_OFFSET_BOT - LABEL_OFFSET) / 2

        # promotions (in same order as `PromoteType`)
        # center the 4 pieces around the middle
        pro_x = HALF_WIDTH - SQUARE_SIZE - HALF_SQUARE_SIZE
        for color in Color:
            tag = f"{color.name.lower()}_promotions"
            x = pro_x
            for promote_type in PromoteType:
                piece_type = promote_type.value
                canvas.create_image(
                    x,
                    bottom_y,
                    image=self._images[color][piece_type],
                    tags=(tag, "promotions"),
                )
                x += SQUARE_SIZE
        self._hide("promotions")

        # state text
        self._state_text = canvas.create_text(
            HALF_WIDTH, bottom_y, font=font20
        )

        def _create_button(coords, text, **kwargs):
            tags_kwargs = {}
            if "tags" in kwargs:
                tags_kwargs["tags"] = kwargs["tags"]
            button_id = canvas.create_rectangle(*coords, **tags_kwargs)
            text_id = canvas.create_text(
                *_button_middle(coords), text=text, **kwargs
            )
            return button_id, text_id

        # reset button
        self._reset_button_coords = (
            10,
            10,
            10 + _button_width(self._font15, "Reset"),
            40,
        )
        _create_button(self._reset_button_coords, "Reset")

        # undo button
        self._undo_button_coords = (
            WIDTH - (10 + _button_width(self._font15, "Undo")),
            10,
            WIDTH - 10,
            40,
        )
        _create_button(self._undo_button_coords, "Undo", tags=("undo",))
        self._hide("undo")

        # pause button
        self._pause_button_coords = (
            WIDTH - (10 + _button_width(self._font15, "Pause")),
            10,
            WIDTH - 10,
            40,
        )
        self._pause_button, self._pause_text = _create_button(
            self._pause_button_coords, "Pause", tags=("pause",)
        )
        self._hide("pause")
        self._paused = False

        # for manually playing with human players
        self._last_move = None
        self._selected = None
        self._other_player_callback = None

    def _show(self, element, **kwargs):
        self._canvas.itemconfig(element, **kwargs, state="normal")

    def _hide(self, element, **kwargs):
        self._canvas.itemconfig(element, **kwargs, state="hidden")

    def _stop_non_human_player(self):
        """Stops any non-human player from thinking."""
        # stop any non-human player from thinking
        if self._other_player_callback is not None:
            self._canvas.after_cancel(self._other_player_callback)
            self._other_player_callback = None

    def _reset(self):
        """Resets the window."""

        # stop any non-human player from thinking
        self._stop_non_human_player()

        # restart the game
        self._game = self._game.restart()

        # reset squares
        self._last_move = None
        self._selected = None
        for square in self._squares.values():
            square.reset()

        # reset other visual stuff
        self._hide("undo")
        self._hide("promotions")
        self._hide(self._state_text)

        if self._has_human_player:
            self._hide("pause")
        else:
            self._show("pause")

        # update piece images
        self._update_pieces()

    def _update_piece_image(
        self,
        piece: Piece,
        img_id: Optional[int] = None,
        pos: Optional[Position] = None,
    ):
        if pos is None:
            pos = piece.pos
        x, y = _brc_to_xy(self._game, pos, center=True)
        if img_id is None:
            # create new image
            img_id = self._canvas.create_image(
                x, y, image=self._images[piece.color][piece.type]
            )
        else:
            # move image to proper location
            self._canvas.coords(img_id, x, y)
            # update the actual image to be the proper piece type
            self._canvas.itemconfig(
                img_id, image=self._images[piece.color][piece.type]
            )
        return img_id

    def _update_pieces(self):
        """Updates the piece images."""
        piece_images = {}
        for piece in self._game.yield_all_pieces():
            img_id = self._piece_images.pop(piece.id, None)
            piece_images[piece.id] = self._update_piece_image(piece, img_id)
        for img_id in self._piece_images.values():
            self._canvas.delete(img_id)
        self._piece_images = piece_images

        # make sure all the "possible move" dots are above the images
        self._canvas.lift("possible_dot")

    def _unselect_piece(self):
        if self._selected is None:
            return
        self._squares[self._selected.pos].reset()
        for move in self._selected.yield_moves():
            self._squares[move.capture_pos].reset_possible()
        self._selected = None

    def _select_piece(self, piece: Piece):
        print("selected piece:", piece)
        self._unselect_piece()
        self._selected = piece
        self._squares[self._selected.pos].select()
        for move in self._selected.yield_moves():
            self._squares[move.capture_pos].possible()

    def _find_undo_state(self):
        # go back until find a state where it's a human player's turn
        self._undo_state = None
        if not self._has_human_player:
            return
        state = self._game
        prev = state.prev
        if prev is None:
            # we're at the first state in the game; can't undo
            pass
        elif prev.current_player.is_human:
            # undo to this state
            self._undo_state = prev
        else:
            # undo to the previous state
            grand_prev = prev.prev
            if grand_prev is None:
                # we're at the second state; can't undo
                pass
            else:
                self._undo_state = grand_prev

    def _click(self, event: _tk.Event):
        """Handles a click event."""
        x, y = event.x, event.y

        # check reset button
        if _within_coords(self._reset_button_coords, x, y):
            self._reset()
            # initialize a non-human turn, if possible
            self._non_human_turn(True)
            return

        if not self._has_human_player:
            # check pause button
            if _within_coords(self._pause_button_coords, x, y):
                self._pause_unpause()

            # nothing else to check
            return

        # check undo button
        if _within_coords(self._undo_button_coords, x, y):
            if self._undo_state is not None:
                self._stop_non_human_player()
                self._game = self._undo_state
                self._update_pieces()
                self._end_turn()
            return

        # check game over
        if self._game.is_game_over():
            return

        if self._game.needs_promotion():
            pro_x = HALF_WIDTH - SQUARE_SIZE * 2
            pro_y = HEIGHT - Y_OFFSET_BOT / 2 - HALF_SQUARE_SIZE
            if not pro_y <= y <= pro_y + SQUARE_SIZE:
                return
            i = int((x - pro_x) / SQUARE_SIZE)
            if not 0 <= i < 4:
                return
            promote_type = PromoteType.by_index(i)
            print("promoting pawn to:", promote_type)
            self._game = self._game.promote(promote_type)
            self._hide("promotions")
            self._end_turn()
            return

        # if not a human player's turn, ignore
        if not self._game.current_player.is_human:
            return

        clicked_pos = _xy_to_brc(self._game, x, y)
        if clicked_pos is None:
            # invalid coords
            return

        piece = self._game.get_piece(*clicked_pos)

        # selecting a new piece
        if self._selected is None:
            if piece is None:
                return
            if piece.color is not self._game.current_color:
                return
            print("=" * 15)
            print("clicked:", clicked_pos, clicked_pos.pos)
            self._select_piece(piece)
            return

        # selecting a different piece
        if piece is not None and piece.color is self._game.current_color:
            if piece is self._selected:
                # clicked same piece; unselect it
                self._unselect_piece()
            else:
                print("=" * 15)
                print("clicked:", clicked_pos, clicked_pos.pos)
                self._select_piece(piece)
            return

        if not self._selected.can_make_move(*clicked_pos):
            # invalid move for selected piece
            return

        # make move
        print("=" * 15)
        print("moving selected to:", clicked_pos, clicked_pos.pos)
        try:
            _, r, c = clicked_pos
            move = (self._selected.pos, (r, c))
            self._game = self._game.make_move(move)
        except ValueError as e:
            print(" ", "ERROR:", e)
            return

        # if needs promotion, wait
        if self._game.needs_promotion():
            pawn = self._selected
            # move the pawn forward to the clicked position
            self._piece_images[pawn.id] = self._update_piece_image(
                pawn, self._piece_images.get(pawn.id, None), pos=clicked_pos
            )
            # delete the captured piece
            if self._game.move.move_captured:
                img_id = self._piece_images.pop(
                    self._game.move.piece_captured.id, None
                )
                if img_id is not None:
                    self._canvas.delete(img_id)
            # reset the piece's possible dots
            for move in pawn.yield_moves():
                self._squares[move.capture_pos].reset_possible()
            # show promotion images
            self._show(f"{self._selected.color.name.lower()}_promotions")
            return

        self._end_turn()

    def _pause_unpause(self):
        if self._game.is_game_over():
            # do nothing
            return

        if self._paused:
            # unpause
            button_text = "Pause"
            # initialize a non-human turn
            self._non_human_turn()
        else:
            # pause
            button_text = "Unpause"
            # stop the current turn
            self._stop_non_human_player()
            # update the state text
            if self._game.is_in_check():
                state_text = f"{self._game.current_color.title()} is in check."
                self._canvas.itemconfig(self._state_text, text=state_text)
            else:
                self._hide(self._state_text)

        # update button text
        self._pause_button_coords = (
            WIDTH - (10 + _button_width(self._font15, button_text)),
            10,
            WIDTH - 10,
            40,
        )
        self._canvas.coords(self._pause_button, self._pause_button_coords)
        self._canvas.coords(
            self._pause_text, _button_middle(self._pause_button_coords)
        )
        self._canvas.itemconfig(self._pause_text, text=button_text)

        self._paused = not self._paused

    def _non_human_turn(self, first_move: bool = False):
        if self._game.current_player.is_human:
            return
        if self._game.is_game_over():
            return

        def make_turn():
            self._game = self._game.step()
            print("non-human player made move:", self._game.move)
            self._other_player_callback = None
            self._end_turn()

        if not first_move and self._delay > 0:
            if self._game.is_in_check():
                action = "is in check. Thinking..."
            else:
                action = "thinking..."
            text = f"{self._game.current_color.title()} {action}"
            self._show(self._state_text, text=text)
            self._other_player_callback = self._canvas.after(
                self._delay, make_turn
            )
        else:
            make_turn()

    def _end_turn(self):
        self._hide(self._state_text, text="")

        self._find_undo_state()
        if self._undo_state is not None:
            self._show("undo")
        else:
            self._hide("undo")

        self._update_pieces()

        self._unselect_piece()
        if self._last_move is not None:
            self._squares[self._last_move].reset()

        # highlight the last move
        if self._game.prev is None:
            # no last move
            self._last_move = None
        else:
            last_pos = self._game.move.result_pos
            self._squares[last_pos].last_move()
            self._last_move = last_pos

        game = self._game
        game.debug()
        # check for game over
        if game.is_game_over():
            # no more pause
            self._hide("pause")
            if game.is_in_checkmate():
                text = f"Checkmate. {game.winner().title()} won!"
            elif game.is_in_stalemate():
                text = "Stalemate."
            elif game.is_draw():
                text = f"Draw ({game.end_game_state.human_readable()})."
            self._show(self._state_text, text=text)
            return

        # check for check
        if game.is_in_check():
            self._show(
                self._state_text,
                text=f"{game.current_color.title()} is in check.",
            )

        # initialize next turn
        self._non_human_turn()

    def run(self):
        """Runs the game."""
        self._reset()

        # bind clicks
        self._canvas.bind_all("<Button-1>", self._click)

        # initialize a non-human turn, if possible
        # if no human players, this will keep going forever until the
        # game is over
        # use an `after` call so that the mainloop is still entered even
        # if there are no human players
        self._canvas.after(0, self._non_human_turn, True)

        self._tk.mainloop()
