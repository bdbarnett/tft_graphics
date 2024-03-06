"""
proverbs.py
===========

.. figure:: ../_static/proverbs.jpg
    :align: center

    Test for TrueType write_font_converter.

Displays what I hope are chinese proverbs in simplified chinese to test UTF-8 font support.
The fonts were converted from True Type fonts using the
:ref:`write_font_converter.py<write_font_converter>` utility.

.. literalinclude:: ../../../examples/proverbs/make_proverbs_fonts.sh


.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `tft_graphics`
    - `board_config`
    - `proverbs_20`
    - `proverbs_30`

"""

import utime
from tft_graphics import Graphics
from board_config import display_drv
import proverbs_20 as font20
import proverbs_30 as font30


tft = Graphics(display_drv, rotation=1)


def color_wheel(WheelPos):
    """returns a 565 color from the given position of the color wheel"""
    WheelPos = (255 - WheelPos) % 255

    if WheelPos < 85:
        return Graphics.color565(255 - WheelPos * 3, 0, WheelPos * 3)

    if WheelPos < 170:
        WheelPos -= 85
        return Graphics.color565(0, WheelPos * 3, 255 - WheelPos * 3)

    WheelPos -= 170
    return Graphics.color565(WheelPos * 3, 255 - WheelPos * 3, 0)


def main():
    proverbs = [
        "万事起头难",
        "熟能生巧",
        "冰冻三尺，非一日之寒",
        "三个臭皮匠，胜过诸葛亮",
        "今日事，今日毕",
        "师父领进门，修行在个人",
        "一口吃不成胖子",
        "欲速则不达",
        "百闻不如一见",
        "不入虎穴，焉得虎子",
    ]

    font = font20 if tft.width < 239 else font30
    line_height = font.HEIGHT + 8
    half_height = tft.height // 2
    half_width = tft.width // 2
    wheel = 0

    while True:
        for proverb in proverbs:
            proverb_lines = proverb.split("，")
            half_lines_height = len(proverb_lines) * line_height // 2

            tft.fill(Graphics.BLACK)

            for count, proverb_line in enumerate(proverb_lines):
                half_length = tft.write_width(font, proverb_line) // 2

                tft.write(
                    font,
                    proverb_line,
                    half_width - half_length,
                    half_height - half_lines_height + count * line_height,
                    color_wheel(wheel),
                )

            wheel = (wheel + 5) % 256

            # pause to slow down scrolling
            utime.sleep(5)


main()
