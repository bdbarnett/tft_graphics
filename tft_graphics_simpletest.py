import random
from board_config import display_drv
from tft_graphics import Graphics

try:
    from machine import Timer
    timed = True
except ImportError:
    timed = False


tft = Graphics(display_drv, rotation=1)

# Define the blocks
block_size = 64   # Size of each dimension in pixels
blocks = [x << 8 | x for x in range(256)]
# blocks = [tft.color565(r,g,b) for r in [0,255] for g in [0,255] for b in [0,255]]
blocks_per_screen = (tft.width * tft.height) / (block_size * block_size)

# Maximum start positions of blocks
max_x = tft.width - block_size - 1
max_y = tft.height - block_size - 1

# Counter and function to show blocks per second
block_count = 0
iter_count = 0
def print_count(_):
    global block_count, iter_count
    iter_count += 1
    print(f"\x08\x08\x08\x08{(block_count // iter_count):4}", end ="")

# Prepare for the loop
print(f"{block_size}x{block_size} blocks per screen: {blocks_per_screen:.2f}")
if timed:
    print(f"Blocks per second:     ", end="")
    tim = Timer(-1)
    tim.init(mode=Timer.PERIODIC, freq=1, callback=print_count)

# Infinite loop
while True:
    tft.fill_rect(
        random.randint(0, max_x),  # x position
        random.randint(0, max_y),  # y position
        block_size,                # width
        block_size,                # height
        random.choice(blocks))     # block color
    block_count += 1
