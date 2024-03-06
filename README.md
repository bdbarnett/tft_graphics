# TFT Graphics
A port of [Russ Hughes's st7789py_mpy](https://github.com/russhughes/st7789py_mpy) with the display driver data removed so that it works with [MPDisplay](https://github.com/bdbarnett/mpdisplay).  The examples folder contains modified versions of st7789py_mpy's examples so they will also work with MPDisplay.  I encourage you to look at Russ Hughes's repository for much more information than I am providing here.  It's his work.  I just rewrote it as TFT Graphics so it is compatible with MPDisplay.

To change existing code written for st7789py_mpy to work with TFT Graphics:

Replace
```
import st7789py as st7789
import board_config
```
with:
```
from tft_graphics import Graphics
from board_config import display_drv
```

Replace
```
tft = board_config.config(board_config.TALL)
```
with
```
tft = Graphics(display_drv, rotation=0)
```
or replace
```
tft = board_config.config(board_config.WIDE)
```
with
```
tft = Graphics(display_drv, rotation=1)
```

In the rest of your file(s), search and replace `st7789.` with `Graphics.`
