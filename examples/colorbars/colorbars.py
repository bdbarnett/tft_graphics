"""
.. _colorbars.py:

colorbars.py
=============

.. figure:: ../_static/colorbars.jpg
    :align: center

    Test bitmap colors.

Displays WHITE, YELLOW, CYAN, GREEN, MAGENTA, RED, and BLUE color bar bitmap named
colorbars_{WIDTH}x(HEIGHT) on the display. Custom sized bitmap modules can be created
using the :ref:`make_colorbars_bitmap.py<make_colorbars_bitmap>` utility.

.. note:: This example requires the following modules:

  .. hlist::
    :columns: 3

    - `tft_graphics`
    - `board_config`
    - `colorbars_{WIDTH}x{HEIGHT}`

"""

from tft_graphics import Graphics
from board_config import display_drv

tft = Graphics(display_drv, rotation=1)
mod_name = f"colorbars_{tft.width}x{tft.height}"
colorbars = __import__(mod_name)
tft.pbitmap(colorbars, 0, 0)
