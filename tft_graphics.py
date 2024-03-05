"""
MIT License

Copyright (c) 2024 Brad Barnett

Copyright (c) 2020-2023 Russ Hughes

Copyright (c) 2019 Ivan Belokobylskiy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

The driver is based on devbis' tft_graphics_mpy module from
https://github.com/devbis/tft_graphics_mpy.

This driver supports:

- Display rotation
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing text using converted TrueType fonts.
- Drawing converted bitmaps
- Named color constants

  - BLACK
  - BLUE
  - RED
  - GREEN
  - CYAN
  - MAGENTA
  - YELLOW
  - WHITE

"""

from math import sin, cos

#
# This allows sphinx to build the docs
#

try:
    from time import sleep_ms
except ImportError:
    sleep_ms = lambda ms: None
    uint = int
    const = lambda x: x

    class micropython:
        @staticmethod
        def viper(func):
            return func

        @staticmethod
        def native(func):
            return func


#
# If you don't need to build the docs, you can remove all of the lines between
# here and the comment above except for the "from time import sleep_ms" line.
#

import struct


_BIT7 = const(0x80)
_BIT6 = const(0x40)
_BIT5 = const(0x20)
_BIT4 = const(0x10)
_BIT3 = const(0x08)
_BIT2 = const(0x04)
_BIT1 = const(0x02)
_BIT0 = const(0x01)


def _rgb565(r, g=0, b=0):
    # Convert r, g, b in range 0-255 to a 16 bit color value RGB565
    # rrrrrggg gggbbbbb
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def _rgb565_swapped(r, g=0, b=0):
    # Convert r, g, b in range 0-255 to a 16 bit color value RGB565
    # ggbbbbbb rrrrrggg
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    color = _rgb565(r, g, b)
    return (color & 0xFF) << 8 | (color & 0xFF00) >> 8


# _bgr565 and _bgr565_swapped are not used in this module but are left here
# in case they are needed in the future.
def _bgr565(r, g=0, b=0):
    # Convert r, g, b in range 0-255 to a 16 bit color value RGB565
    # bbbbbggg gggrrrrr
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    return ((b & 0xF8) << 8) | ((g & 0xFC) << 3) | (r >> 3)


def _bgr565_swapped(r, g=0, b=0):
    # Convert r, g, b in range 0-255 to a 16 bit color value RGB565
    # gggrrrrr bbbbbggg
    if isinstance(r, (tuple, list)):
        r, g, b = r[:3]
    color = _bgr565(r, g, b)
    return (color & 0xFF) << 8 | (color & 0xFF00) >> 8


class Graphics:
    """
    Graphics class

    Args:
        display_drv (BusDisplay): BusDisplay object **Required**
        rotation (int): Display rotation (0-3) **Optional**
    """

    WHITE = const(
        0xFFFF
    )  # White and black must be defined here for use as defaults in methods below
    BLACK = const(
        0x0000
    )  # as well as for use by the user before a Graphics object is instantiated.

    @classmethod
    def _set_color_func(cls, needs_swap):
        """
        Set the color565 function to the appropriate one for byte swapping
        and set the color constants to the appropriate values.
        """
        if needs_swap:
            cls.color565 = _rgb565_swapped
        else:
            cls.color565 = _rgb565

        cls.RED = cls.color565(255, 0, 0)
        cls.GREEN = cls.color565(0, 255, 0)
        cls.BLUE = cls.color565(0, 0, 255)
        cls.CYAN = cls.color565(0, 255, 255)
        cls.MAGENTA = cls.color565(255, 0, 255)
        cls.YELLOW = cls.color565(255, 255, 0)

    def __init__(self, display_drv, rotation=None):
        """
        Initialize Graphics.
        """
        self.display_drv = display_drv
        if rotation is not None:
            self.rotation(rotation)

        # If byte swapping is required and the display bus is capable of having byte swapping disabled,
        # disable it and set a flag so we can swap the color bytes as they are created.
        if self.display_drv.requires_byte_swap:
            self.needs_swap = self.display_drv.bus_swap_disable(True)
        else:
            self.needs_swap = False

        # Set the Graphics.color565 function to the appropriate one for byte swapping
        self._set_color_func(self.needs_swap)

    @property
    def width(self):
        return self.display_drv.width

    @property
    def height(self):
        return self.display_drv.height

    def hard_reset(self):
        """
        Hard reset display.
        """
        self.display_drv.hard_reset()

    def soft_reset(self):
        """
        Soft reset display.
        """
        self.display_drv.soft_reset()

    def sleep_mode(self, value):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        self.display_drv.sleep_mode(value)

    def inversion_mode(self, value):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
        self.display_drv.invert_colors(value)

    def rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation (int):
                - 0-Portrait
                - 1-Landscape
                - 2-Inverted Portrait
                - 3-Inverted Landscape

            custom_rotations can have any number of rotations
        """
        self.display_drv.rotation = rotation * 90

    def vscrdef(self, tfa, vsa, bfa):
        """
        Set Vertical Scrolling Definition.

        To scroll a 135x240 display these values should be 40, 240, 40.
        There are 40 lines above the display that are not shown followed by
        240 lines that are shown followed by 40 more lines that are not shown.
        You could write to these areas off display and scroll them into view by
        changing the TFA, VSA and BFA values.

        Args:
            tfa (int): Top Fixed Area
            vsa (int): Vertical Scrolling Area
            bfa (int): Bottom Fixed Area
        """
        self.display_drv.vscrdef(tfa, vsa, bfa)

    def vscsad(self, vssa):
        """
        Set Vertical Scroll Start Address of RAM.

        Defines which line in the Frame Memory will be written as the first
        line after the last line of the Top Fixed Area on the display

        Example:

            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)

        Args:
            vssa (int): Vertical Scrolling Start Address

        """
        self.display_drv.vscsad(vssa)

    def fill_rect(self, x, y, width, height, color):
        """
        Draw a rectangle at the given location, size and filled with color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self.display_drv.fill_rect(x, y, width, height, color)

    def fill(self, color):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        self.fill_rect(0, 0, self.width, self.height, color)

    def vline(self, x, y, length, color):
        """
        Draw vertical line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, 1, length, color)

    def hline(self, x, y, length, color):
        """
        Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, length, 1, color)

    def rect(self, x, y, w, h, color):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self.hline(x, y, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)
        self.hline(x, y + h - 1, w, color)

    def blit_buffer(self, buffer, x, y, width, height):
        """
        Copy buffer to display at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
        """
        self.display_drv.blit(x, y, width, height, buffer)

    def pixel(self, x, y, color):
        """
        Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        self.blit_buffer(struct.pack(">H", color), x, y, 1, 1)

    def line(self, x0, y0, x1, y1, color):
        """
        Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.

        Args:
            x0 (int): Start point x coordinate
            y0 (int): Start point y coordinate
            x1 (int): End point x coordinate
            y1 (int): End point y coordinate
            color (int): 565 encoded color
        """
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        while x0 <= x1:
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    @micropython.native
    def polygon(self, points, x, y, color, angle=0, center_x=0, center_y=0):
        """
        Draw a polygon on the display.

        Args:
            points (list): List of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): 565 encoded color.
            angle (float): Rotation angle in radians (default: 0).
            center_x (int): X-coordinate of the rotation center (default: 0).
            center_y (int): Y-coordinate of the rotation center (default: 0).

        Raises:
            ValueError: If the polygon has less than 3 points.
        """
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points.")

        # fmt: off
        if angle:
            cos_a = cos(angle)
            sin_a = sin(angle)
            rotated = [
                (x + center_x + int((point[0] - center_x) * cos_a - (point[1] - center_y) * sin_a),
                 y + center_y + int((point[0] - center_x) * sin_a + (point[1] - center_y) * cos_a))
                for point in points
            ]
        else:
            rotated = [(x + int((point[0])), y + int((point[1]))) for point in points]

        for i in range(1, len(rotated)):
            self.line(rotated[i - 1][0], rotated[i - 1][1], rotated[i][0], rotated[i][1], color)

    # fmt: on

    def bitmap(self, bitmap, x, y, index=0):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module
        """
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        if self.width <= to_col or self.height <= to_row:
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        palette = bitmap.PALETTE
        needs_swap = self.needs_swap
        buffer = bytearray(buffer_len)

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap.BITMAP[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]
            if needs_swap:
                buffer[i] = color & 0xFF
                buffer[i + 1] = color >> 8
            else:
                buffer[i] = color >> 8
                buffer[i + 1] = color & 0xFF

        self.blit_buffer(buffer, x, y, width, height)

    def pbitmap(self, bitmap, x, y, index=0):
        """
        Draw a bitmap on display at the specified column and row one row at a time

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module

        """
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        bitmap_size = height * width
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        palette = bitmap.PALETTE
        needs_swap = self.needs_swap
        buffer = bytearray(bitmap.WIDTH * 2)

        for row in range(height):
            for col in range(width):
                color_index = 0
                for _ in range(bpp):
                    color_index <<= 1
                    color_index |= (
                        bitmap.BITMAP[bs_bit // 8] & 1 << (7 - (bs_bit % 8))
                    ) > 0
                    bs_bit += 1
                color = palette[color_index]
                if needs_swap:
                    buffer[col * 2] = color & 0xFF
                    buffer[col * 2 + 1] = color >> 8 & 0xFF
                else:
                    buffer[col * 2] = color >> 8 & 0xFF
                    buffer[col * 2 + 1] = color & 0xFF

            to_col = x + width - 1
            to_row = y + row
            if self.width > to_col and self.height > to_row:
                self.blit_buffer(buffer, x, y + row, width, height)

    def write(self, font, string, x, y, fg=WHITE, bg=BLACK):
        """
        Write a string using a converted true-type font on the display starting
        at the specified column and row

        Args:
            font (font): The module containing the converted true-type font
            s (string): The string to write
            x (int): column to start writing
            y (int): row to start writing
            fg (int): foreground color, optional, defaults to WHITE
            bg (int): background color, optional, defaults to BLACK
        """
        buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
        buffer = bytearray(buffer_len)
        fg_hi = fg >> 8
        fg_lo = fg & 0xFF

        bg_hi = bg >> 8
        bg_lo = bg & 0xFF

        for character in string:
            try:
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                if font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]

                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]

                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT * 2

                for i in range(0, buffer_needed, 2):
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        buffer[i] = fg_hi
                        buffer[i + 1] = fg_lo
                    else:
                        buffer[i] = bg_hi
                        buffer[i + 1] = bg_lo

                    bs_bit += 1

                to_col = x + char_width - 1
                to_row = y + font.HEIGHT - 1
                if self.width > to_col and self.height > to_row:
                    self.blit_buffer(
                        buffer[:buffer_needed], x, y, char_width, font.HEIGHT
                    )

                x += char_width

            except ValueError:
                pass

    def write_width(self, font, string):
        """
        Returns the width in pixels of the string if it was written with the
        specified font

        Args:
            font (font): The module containing the converted true-type font
            string (string): The string to measure

        Returns:
            int: The width of the string in pixels

        """
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]
            except ValueError:
                pass

        return width

    def text(self, font, text, x0, y0, color=WHITE, background=BLACK):
        """
        Draw text on display in specified font and colors. 8 and 16 bit wide
        fonts are supported.

        Args:
            font (module): font module to use.
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, color, background)
        else:
            self._text16(font, text, x0, y0, color, background)

    def _text8(self, font, text, x0, y0, fg_color=WHITE, bg_color=BLACK):
        """
        Internal method to write characters with width of 8 and
        heights of 8 or 16.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """

        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                if font.HEIGHT == 8:
                    passes = 1
                    size = 8
                    each = 0
                else:
                    passes = 2
                    size = 16
                    each = 8

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack8(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8)

                x0 += 8

    def _text16(self, font, text, x0, y0, fg_color=WHITE, bg_color=BLACK):
        """
        Internal method to draw characters with width of 16 and heights of 16
        or 32.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """

        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                each = 16
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack16(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8)
            x0 += 16

    @micropython.viper
    @staticmethod
    def _pack8(glyphs, idx: uint, fg_color: uint, bg_color: uint):
        buffer = bytearray(128)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 64, 8):
            byte = glyph[idx]
            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer

    @micropython.viper
    @staticmethod
    def _pack16(glyphs, idx: uint, fg_color: uint, bg_color: uint):
        """
        Pack a character into a byte array.

        Args:
            char (str): character to pack

        Returns:
            128 bytes: character bitmap in color565 format
        """

        buffer = bytearray(256)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 128, 16):
            byte = glyph[idx]

            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

            byte = glyph[idx]
            bitmap[i + 8] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 9] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 10] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 11] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 12] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 13] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 14] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 15] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer
