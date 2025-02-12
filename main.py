import time
import random
from cosmic import CosmicUnicorn
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN as DISPLAY

cu = CosmicUnicorn()
graphics = PicoGraphics(DISPLAY)

width = CosmicUnicorn.WIDTH
height = CosmicUnicorn.HEIGHT

total_points = 0

last_drop_time = 0
DEBOUNCE_TIME = 300
last_rotate_time = 0
ROTATE_DEBOUNCE_TIME = 300

last_move_time_left = 0
last_move_time_right = 0
MOVE_DEBOUNCE_TIME = 150

GRID_SIZE = 16
BLOCK_SIZE = 2

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
grid = [[empty for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

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
next_piece = None

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
        if new_y >= 0 and grid[new_y][new_x] != empty:
            return True
    return False

def rotate_piece():
    """Rotates the current piece by 90 degrees around its center, ensuring it stays in place."""
    global current_piece
    
    min_x = min(x for x, y in current_piece["shape"])
    min_y = min(y for x, y in current_piece["shape"])
    max_x = max(x for x, y in current_piece["shape"])
    max_y = max(y for x, y in current_piece["shape"])

    center_x = min_x + (max_x - min_x) // 2
    center_y = min_y + (max_y - min_y) // 2
    
    rotated_shape = []
    for x, y in current_piece["shape"]:
        new_x = center_y - y + center_x
        new_y = x - center_x + center_y
        rotated_shape.append((new_x, new_y))

    original_shape = current_piece["shape"]
    current_piece["shape"] = rotated_shape
    
    if check_collision():
        current_piece["shape"] = original_shape
    else:
        min_x_rot = min(x for x, y in current_piece["shape"])
        if min_x_rot < 0:
            offset = abs(min_x_rot)
            current_piece["shape"] = [(x + offset, y) for x, y in current_piece["shape"]]
        
        if check_collision():
            current_piece["shape"] = original_shape

def move_left():
    global last_move_time_left
    if time.ticks_ms() - last_move_time_left > MOVE_DEBOUNCE_TIME:
        if not check_collision(dx=-1):
            current_piece["x"] -= 1
        last_move_time_left = time.ticks_ms()

def move_right():
    global last_move_time_right
    if time.ticks_ms() - last_move_time_right > MOVE_DEBOUNCE_TIME:
        if not check_collision(dx=1):
            current_piece["x"] += 1
        last_move_time_right = time.ticks_ms()

def move_down():
    """Moves the piece down if it hasn't reached the bottom or another piece."""
    if not check_collision(dy=1):
        current_piece["y"] += 1
    else:
        lock_piece()
        spawn_new_piece()

def handle_rotate():
    """Handles the rotate action with debounce."""
    global last_rotate_time
    if time.ticks_ms() - last_rotate_time > ROTATE_DEBOUNCE_TIME:
        rotate_piece()
        last_rotate_time = time.ticks_ms()

def drop_piece():
    """Drops the piece instantly until it collides, with debounce."""
    global last_drop_time
    if time.ticks_ms() - last_drop_time > DEBOUNCE_TIME:
        while not check_collision(dy=1):
            current_piece["y"] += 1
        lock_piece()
        spawn_new_piece()
        last_drop_time = time.ticks_ms()

def clear_full_rows():
    """Clears full rows, shifts the rows above down, and updates the score."""
    global grid, total_points
    rows_to_clear = []
    
    for y in range(GRID_SIZE):
        if all(grid[y][x] != empty for x in range(GRID_SIZE)):
            rows_to_clear.append(y)
    
    for row in rows_to_clear:
        del grid[row]
        grid.insert(0, [empty for _ in range(GRID_SIZE)])
        total_points += 1

def lock_piece():
    """Locks the current piece in the grid and marks the occupied spaces with its color."""
    for x, y in current_piece["shape"]:
        grid[current_piece["y"] + y][current_piece["x"] + x] = current_piece["color"]
    
    clear_full_rows()

def spawn_new_piece():
    """Spawns a new piece and generates the next piece."""
    global current_piece, next_piece
    if next_piece is None:
        shape, color = random.choice(shapes)
        next_piece = {"shape": shape, "color": color}
    
    current_piece = {
        "x": GRID_SIZE // 2 - 1,
        "y": 0,
        "shape": next_piece["shape"],
        "color": next_piece["color"]
    }
    
    # Generate the next piece
    shape, color = random.choice(shapes)
    next_piece = {"shape": shape, "color": color}

def draw_next_piece():
    """Draws the next piece in the top right corner."""
    if next_piece:
        # Calculate the position for the next piece preview
        preview_x = GRID_SIZE - 3  # 4 blocks from the right edge
        preview_y = 1  # 1 block from the top
        
        for x, y in next_piece["shape"]:
            draw_block(preview_x + x, preview_y + y, next_piece["color"])

def reset_game():
    global grid, total_points
    grid = [[empty for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    total_points = 0
    spawn_new_piece()

def check_game_over():
    return any(grid[0][x] != empty for x in range(GRID_SIZE))

# Spawn the first piece
spawn_new_piece()

last_move_time = time.ticks_ms()

graphics.set_font("bitmap8")
def display_score():
    graphics.set_pen(graphics.create_pen(255, 255, 255))  # White color for the text
    graphics.text(f"{total_points}", 1, 1, scale=1)

while True:
    graphics.clear()

    # Draw grid and current piece
    draw_grid()
    draw_piece()
    
    # OPTIONAL: Display next piece preview
    draw_next_piece()
    
    # OPTIONAL: Display score (lines cleared)
    display_score()

    # Button movement logic
    if cu.is_pressed(CosmicUnicorn.SWITCH_A):
        move_right()
    if cu.is_pressed(CosmicUnicorn.SWITCH_B):
        move_left()
    if cu.is_pressed(CosmicUnicorn.SWITCH_C):
        handle_rotate()
    if cu.is_pressed(CosmicUnicorn.SWITCH_D):
        drop_piece()

    # Apply gravity every 500ms
    if time.ticks_ms() - last_move_time > 500:
        move_down()
        last_move_time = time.ticks_ms()

    # Check for game over
    if check_game_over():
        reset_game()

    cu.update(graphics)
    time.sleep(0.05)
