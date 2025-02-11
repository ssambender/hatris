import time
import random
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN as DISPLAY

cu = CosmicUnicorn()
graphics = PicoGraphics(DISPLAY)

width = CosmicUnicorn.WIDTH
height = CosmicUnicorn.HEIGHT

last_drop_time = 0  # Store the last time the drop button was pressed
DEBOUNCE_TIME = 300  # 300ms debounce period

GRID_SIZE = 16  # 16x16 grid, each block is 2x2 pixels
BLOCK_SIZE = 2  # Each block is 2x2 pixels

# Define colors
yellow = graphics.create_pen(255, 255, 0)
teal = graphics.create_pen(0, 255, 255)
green = graphics.create_pen(0, 255, 0)
red = graphics.create_pen(255, 0, 0)
orange = graphics.create_pen(255, 150, 0)
purple = graphics.create_pen(150, 100, 255)
pink = graphics.create_pen(255, 0, 255)
empty = graphics.create_pen(0, 0, 0)

# Initialize grid (0 = empty, 1 = occupied)
grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Define Tetris shapes with colors
shapes = [
    ([(0,0), (1,0), (0,1), (1,1)], yellow),  # O
    ([(0,0), (0,1), (0,2), (0,3)], teal),  # I
    ([(1,0), (2,0), (0,1), (1,1)], green),  # S
    ([(0,0), (1,0), (1,1), (2,1)], red),  # Z
    ([(0,0), (0,1), (0,2), (1,2)], orange),  # L
    ([(1,0), (1,1), (1,2), (0,2)], purple),  # J
    ([(1,0), (0,1), (1,1), (2,1)], pink)  # T
]

def draw_block(x, y, color):
    """Draw a 2x2 block at grid (x, y)."""
    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:  # Ensure within bounds
        graphics.set_pen(color)
        for dx in range(BLOCK_SIZE):
            for dy in range(BLOCK_SIZE):
                graphics.pixel(x * BLOCK_SIZE + dx, y * BLOCK_SIZE + dy)

def draw_grid():
    """Draws the entire grid based on stored values."""
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            color = grid[y][x]  # Color is now the color stored in the grid
            draw_block(x, y, color)

def draw_piece():
    """Draws the current falling piece."""
    for x, y in current_piece["shape"]:
        draw_block(current_piece["x"] + x, current_piece["y"] + y, current_piece["color"])

# Set brightness
cu.set_brightness(0.5)

def check_collision(dx=0, dy=0):
    """Checks if moving by (dx, dy) would result in a collision."""
    for x, y in current_piece["shape"]:
        new_x = current_piece["x"] + x + dx
        new_y = current_piece["y"] + y + dy
        if new_x < 0 or new_x >= GRID_SIZE or new_y >= GRID_SIZE:
            return True  # Out of bounds collision
        # Check for collision with non-empty space (any color other than empty)
        if grid[new_y][new_x] != empty:
            return True
    return False

def move_left():
    if not check_collision(dx=-1):
        current_piece["x"] -= 1

def move_right():
    if not check_collision(dx=1):
        current_piece["x"] += 1

def move_down():
    """Moves the piece down if it hasn't reached the bottom or another piece."""
    if not check_collision(dy=1):
        current_piece["y"] += 1
    else:
        lock_piece()
        spawn_new_piece()

def drop_piece():
    """Drops the piece instantly until it collides, with debounce."""
    global last_drop_time
    if time.ticks_ms() - last_drop_time > DEBOUNCE_TIME:  # Check if enough time has passed
        while not check_collision(dy=1):
            current_piece["y"] += 1
        lock_piece()
        spawn_new_piece()
        last_drop_time = time.ticks_ms()  # Update the last drop time

def lock_piece():
    """Locks the current piece in the grid and marks the occupied spaces with its color."""
    for x, y in current_piece["shape"]:
        grid[current_piece["y"] + y][current_piece["x"] + x] = current_piece["color"]

def spawn_new_piece():
    """Spawns a new random piece at the top."""
    global current_piece
    shape, color = random.choice(shapes)
    current_piece = {
        "x": GRID_SIZE // 2 - 1,
        "y": 0,
        "shape": shape,
        "color": color
    }

# Spawn the first piece
spawn_new_piece()

last_move_time = time.ticks_ms()

while True:
    graphics.clear()
    
    # Draw grid and current piece
    draw_grid()
    draw_piece()

    # Button movement logic
    if cu.is_pressed(CosmicUnicorn.SWITCH_A):
        move_left()
    if cu.is_pressed(CosmicUnicorn.SWITCH_B):
        move_right()
    if cu.is_pressed(CosmicUnicorn.SWITCH_D):
        drop_piece()
    
    # Apply gravity every 500ms
    if time.ticks_ms() - last_move_time > 500:
        move_down()
        last_move_time = time.ticks_ms()
    
    cu.update(graphics)
    time.sleep(0.05)

