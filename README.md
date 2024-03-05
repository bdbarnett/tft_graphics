# TFT Graphics
A port of Russ Hughes's st7789py with the display driver data removed so that it works with MPDisplay.  The examples folder contains modified versions of st7789py's examples so they will
also work with MPDisplay.  To change existing code written for st7789py to work with TFT Graphics:

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
