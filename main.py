from ursina import *
import os

from core.bloxorz_core import BloxorzCore
from core.board import load_stage

app = Ursina()

# Đọc map từ folder stages
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(current_dir, "stages", "stage1.txt")
    matrix, start_row, start_col = load_stage(map_path)
except Exception:
    matrix = [[1, 1, 1, 0, 0], [1, 1, 1, 1, 0], [1, 1, 1, 2, 0]]
    start_row, start_col = 0, 0

game = BloxorzCore(matrix, start_row, start_col)

# Cam
center_x = len(matrix[0]) / 2.0
center_z = len(matrix) / 2.0
camera.position = (center_x, 14, center_z - 12)
camera.look_at((center_x, 0, center_z))

# Vẽ board
for r in range(len(matrix)):
    for c in range(len(matrix[0])):
        val = matrix[r][c]
        if val == 1:  
            Entity(model='cube', color=color.cyan, texture='brick', position=(c, 0, r), scale=(0.95, 0.2, 0.95))
        elif val == 2:  
            Entity(model='cube', color=color.red, texture='brick', position=(c, -0.05, r), scale=(0.95, 0.1, 0.95))

# Vẽ block
block = Entity(model='cube', color=color.white, texture='brick')

game_over = False
is_falling = False
fall_speed = 0.0
delay_timer = 0.0

def update_block_visuals():
    r, c = game.r, game.c
    ori = game.orientation
    
    # Cập nhật vị trí và kích thước block
    if ori == 'STANDING':
        block.scale = (0.95, 2.0, 0.95)
        block.position = (c, 1.1, r)
        block.texture_scale = (1, 2)
    elif ori == 'LYING_H':
        block.scale = (2.0, 0.95, 0.95)
        block.position = (c + 0.5, 0.575, r)
        block.texture_scale = (2, 1)
    elif ori == 'LYING_V':
        block.scale = (0.95, 0.95, 2.0)
        block.position = (c, 0.575, r + 0.5)
        block.texture_scale = (1, 2)

update_block_visuals()

status_text = Text(text="Di chuyển: W, A, S, D | Reset: R", position=(-0.85, 0.45), scale=1.3, color=color.white)

# Update
def update():
    global is_falling, fall_speed, delay_timer
    
    # Delay
    if delay_timer > 0:
        delay_timer -= time.dt
        if delay_timer <= 0:
            if game.fall_void_cell is not None:
                game.orientation = 'STANDING'
                game.r, game.c = game.fall_void_cell
                update_block_visuals()
            
            is_falling = True
            fall_speed = 0.0

    # Rơi
    if is_falling:
        fall_speed += 18.0 * time.dt  
        block.y -= fall_speed * time.dt

def input(key):
    global game_over, is_falling, fall_speed, delay_timer
    
    # Khóa control
    if game_over and key != 'r':
        return

    # Xử lý movement
    if key in ['w', 'up arrow']:
        status = game.move('DOWN')
    elif key in ['s', 'down arrow']:
        status = game.move('UP')
    elif key in ['a', 'left arrow']:
        status = game.move('LEFT')
    elif key in ['d', 'right arrow']:
        status = game.move('RIGHT')
    elif key == 'r':  
        game.r, game.c, game.orientation = start_row, start_col, 'STANDING'
        status = "CONTINUE"
        game_over = False
        is_falling = False
        fall_speed = 0.0
        delay_timer = 0.0
        game.fall_void_cell = None
    else:
        return

    update_block_visuals()

    # Update trạng thái game
    if status == "WIN":
        status_text.text = "<green>CHIẾN THẮNG! Khối đã lọt vào hố!"
        game_over = True
    elif status == "LOSE_FALL":
        status_text.text = "<red>GAME OVER! Bấm R để chơi lại"
        game_over = True
        delay_timer = 0.25
    else:
        status_text.text = f"Hướng: {game.orientation} | Vị trí ô: ({game.r}, {game.c})"

if __name__ == '__main__':
    app.run()