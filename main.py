from ursina import *
import os

from core.bloxorz_core import BloxorzCore
from core.board import load_stage, to_switch_dicts
from solvers import bfs_solver, dfs_solver, ucs_solver
try:
    from solvers import astar_solver
except Exception:
    astar_solver = None

app = Ursina()

# Đọc map từ folder stages (hỗ trợ fragile/bridge/switch)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(current_dir, "stages", "stage_demo_split.txt")
    board, start_row, start_col = load_stage(map_path)
    matrix = board.grid
except Exception:
    matrix = [[1, 1, 1, 0, 0], [1, 1, 1, 1, 0], [1, 1, 1, 2, 0]]
    start_row, start_col = 0, 0
    board = None

def _split_dicts(b):
    if not b:
        return None
    return [{'r': s.r, 'c': s.c, 'target_a': s.target_a, 'target_b': s.target_b}
            for s in b.split_switches]

game = BloxorzCore(
    matrix, start_row, start_col,
    switches=to_switch_dicts(board.switches) if board else None,
    bridge_groups=board.bridge_groups if board else None,
    initial_open_bridges=board.initial_open_bridges if board else None,
    split_switches=_split_dicts(board),
)

# Cam
center_x = len(matrix[0]) / 2.0
center_z = len(matrix) / 2.0
camera.position = (center_x, 14, center_z - 12)
camera.look_at((center_x, 0, center_z))

# --- Vẽ board ---
tile_entities = {}

def color_for_tile(val, is_open_bridge=False):
    if val == 1:
        return color.cyan
    elif val == 2:
        return color.red
    elif val == 3:
        return color.orange
    elif val == 4:
        return color.green if is_open_bridge else color.gray
    elif val == 5:
        return color.azure
    elif val == 6:
        return color.violet
    elif val == 7:
        return color.magenta
    return color.cyan

for r in range(len(matrix)):
    for c in range(len(matrix[0])):
        val = matrix[r][c]
        if val == 0:
            continue
        is_open = (r, c) in game.open_bridges
        y = 0 if val != 2 else -0.05
        h = 0.2 if val != 2 else 0.1
        ent = Entity(model='cube', color=color_for_tile(val, is_open), texture='brick',
                      position=(c, y, r), scale=(0.95, h, 0.95))
        tile_entities[(r, c)] = ent

def refresh_bridge_colors():
    for (r, c), ent in tile_entities.items():
        if matrix[r][c] == 4:
            ent.color = color.green if (r, c) in game.open_bridges else color.gray

# Vẽ block
block = Entity(model='cube', color=color.white, texture='brick')

# Hai cube 1x1x1 dùng khi split — ẩn mặc định, chỉ hiện khi game.split_mode
cube_a = Entity(model='cube', color=color.white, texture='brick', scale=(0.9, 0.9, 0.9), enabled=False)
cube_b = Entity(model='cube', color=color.white, texture='brick', scale=(0.9, 0.9, 0.9), enabled=False)
ACTIVE_CUBE_COLOR = color.yellow
INACTIVE_CUBE_COLOR = color.white.tint(-.3)

game_over = False
is_falling = False
fall_speed = 0.0
delay_timer = 0.0

# --- Trạng thái Solve/animation ---
is_solving = False         # đang phát lại animation, khóa input thủ công
solve_queue = []           # danh sách action còn lại cần phát
solve_step_timer = 0.0
SOLVE_STEP_INTERVAL = 0.35  # giây giữa mỗi nước đi khi animate


def update_block_visuals():
    if game.split_mode:
        block.enabled = False
        cube_a.enabled = True
        cube_b.enabled = True
        cube_a.position = (game.cubes[0]['c'], 0.45, game.cubes[0]['r'])
        cube_b.position = (game.cubes[1]['c'], 0.45, game.cubes[1]['r'])
        cube_a.color = ACTIVE_CUBE_COLOR if game.active_cube_index == 0 else INACTIVE_CUBE_COLOR
        cube_b.color = ACTIVE_CUBE_COLOR if game.active_cube_index == 1 else INACTIVE_CUBE_COLOR
        return

    cube_a.enabled = False
    cube_b.enabled = False
    block.enabled = True

    r, c = game.r, game.c
    ori = game.orientation

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

status_text = Text(text="Di chuyển: W, A, S, D | Reset: R | Đổi cube: Space (khi split)",
                    position=(-0.85, 0.45), scale=1.1, color=color.white)
solve_info_text = Text(text="", position=(-0.85, 0.40), scale=1.0, color=color.yellow)


def reset_game():
    global game_over, is_falling, fall_speed, delay_timer, is_solving, solve_queue, solve_step_timer
    game.r, game.c, game.orientation = start_row, start_col, 'STANDING'
    game.open_bridges = set(board.initial_open_bridges) if board else set()
    game.fall_void_cell = None
    game.split_mode = False
    game.cubes = []
    game.active_cube_index = 0
    game_over = False
    is_falling = False
    fall_speed = 0.0
    delay_timer = 0.0
    is_solving = False
    solve_queue = []
    solve_step_timer = 0.0
    update_block_visuals()
    refresh_bridge_colors()
    status_text.text = "Di chuyển: W, A, S, D | Reset: R | Đổi cube: Space (khi split)"


def run_algorithm(name, solve_fn):
    """Reset về start, chạy thuật toán, rồi animate lại đường đi tìm được."""
    global is_solving, solve_queue

    if board is None:
        solve_info_text.text = "<red>Không có board hợp lệ để giải."
        return

    reset_game()  # luôn giải từ vị trí start của màn, không phải vị trí hiện tại

    solve_info_text.text = f"Đang tính {name}..."
    try:
        path, nodes_expanded = solve_fn(board, start_row, start_col)
    except Exception as e:
        solve_info_text.text = f"<red>{name} lỗi: {e}"
        return

    if not path:
        solve_info_text.text = f"<red>{name}: không tìm được lời giải."
        return

    solve_info_text.text = f"<green>{name}: {len(path)} bước, mở rộng {nodes_expanded} node. Đang phát lại..."
    solve_queue = list(path)
    is_solving = True


def on_solve_bfs():
    run_algorithm("BFS", bfs_solver.solve)

def on_solve_dfs():
    run_algorithm("DFS/IDS", dfs_solver.ids)

def on_solve_ucs():
    run_algorithm("UCS", ucs_solver.solve)

def on_solve_astar():
    if astar_solver is None or not hasattr(astar_solver, 'solve'):
        solve_info_text.text = "<red>A* chưa được cài đặt."
        return
    run_algorithm("A*", astar_solver.solve)


# --- Nút bấm ---
btn_bfs = Button(text='Solve BFS', color=color.azure, scale=(0.15, 0.05),
                  position=(0.62, 0.45), on_click=on_solve_bfs)
btn_dfs = Button(text='Solve DFS', color=color.azure, scale=(0.15, 0.05),
                  position=(0.62, 0.38), on_click=on_solve_dfs)
btn_ucs = Button(text='Solve UCS', color=color.azure, scale=(0.15, 0.05),
                  position=(0.62, 0.31), on_click=on_solve_ucs)
btn_astar = Button(text='Solve A*', color=color.azure, scale=(0.15, 0.05),
                    position=(0.62, 0.24), on_click=on_solve_astar)
btn_reset = Button(text='Reset', color=color.red.tint(-.2), scale=(0.15, 0.05),
                    position=(0.62, 0.15), on_click=reset_game)


def update():
    global is_falling, fall_speed, delay_timer, is_solving, solve_queue, solve_step_timer

    if delay_timer > 0:
        delay_timer -= time.dt
        if delay_timer <= 0:
            if game.fall_void_cell is not None:
                game.orientation = 'STANDING'
                game.r, game.c = game.fall_void_cell
                update_block_visuals()
            is_falling = True
            fall_speed = 0.0

    if is_falling:
        fall_speed += 18.0 * time.dt
        block.y -= fall_speed * time.dt

    # --- Phát animation của solver ---
    if is_solving and not game_over:
        solve_step_timer -= time.dt
        if solve_step_timer <= 0:
            solve_step_timer = SOLVE_STEP_INTERVAL
            if solve_queue:
                action = solve_queue.pop(0)
                status = game.move(action)
                update_block_visuals()
                refresh_bridge_colors()
                if status == "WIN":
                    status_text.text = "<green>CHIẾN THẮNG! Khối đã lọt vào hố!"
                    globals()['game_over'] = True
                    is_solving = False
                elif status == "LOSE_FALL":
                    status_text.text = "<red>GAME OVER! Bấm R để chơi lại"
                    globals()['game_over'] = True
                    is_solving = False
                    delay_timer = 0.25
                else:
                    status_text.text = f"Hướng: {game.orientation} | Vị trí ô: ({game.r}, {game.c})"
            else:
                is_solving = False


def input(key):
    global game_over, is_falling, fall_speed, delay_timer

    if is_solving:
        return  # khóa input thủ công trong lúc đang phát animation

    if key == 'space':
        game.switch_active_cube()
        update_block_visuals()
        return

    if game_over and key != 'r':
        return

    if key in ['w', 'up arrow']:
        status = game.move('DOWN')
    elif key in ['s', 'down arrow']:
        status = game.move('UP')
    elif key in ['a', 'left arrow']:
        status = game.move('LEFT')
    elif key in ['d', 'right arrow']:
        status = game.move('RIGHT')
    elif key == 'r':
        reset_game()
        return
    else:
        return

    update_block_visuals()
    refresh_bridge_colors()

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
