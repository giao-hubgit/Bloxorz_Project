import os
import time as pytime
import tracemalloc

from ursina import *

from core.bloxorz_core import BloxorzCore
from core.board import load_stage, to_switch_dicts, split_dicts
from core.state import VOID, FLOOR, GOAL, FRAGILE, BRIDGE, SOFT_SWITCH, HEAVY_SWITCH, SPLIT_SWITCH
from solvers import bfs_solver, dfs_solver, ucs_solver
try:
    from solvers import astar_solver
except Exception:
    astar_solver = None

app = Ursina()

STAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stages")
DEFAULT_STAGE = os.path.join(STAGES_DIR, "stage1.txt")

game = None
board = None
start_row = start_col = 0
tile_entities = {}
fragile_cells = []
block = None
cube_a = cube_b = None

game_over = False
is_falling = False
fall_speed = 0.0
delay_timer = 0.0

is_solving = False
solve_queue = []
solve_step_timer = 0.0
SOLVE_STEP_INTERVAL = 0.35

status_text = None
solve_info_text = None
stats_text = None

def build_level(path):
    global game, board, start_row, start_col, tile_entities, fragile_cells
    global block, cube_a, cube_b

    for ent in list(tile_entities.values()):
        destroy(ent)
    tile_entities = {}
    if block is not None:
        destroy(block)
    if cube_a is not None:
        destroy(cube_a)
        destroy(cube_b)

    board, start_row, start_col = load_stage(path)
    matrix = board.grid

    game = BloxorzCore(
        matrix, start_row, start_col,
        switches=to_switch_dicts(board.switches),
        bridge_groups=board.bridge_groups,
        initial_open_bridges=board.initial_open_bridges,
        split_switches=split_dicts(board.split_switches),
    )

    center_x = len(matrix[0]) / 2.0
    center_z = len(matrix) / 2.0
    camera.position = (center_x, 14, center_z - 12)
    camera.look_at((center_x, 0, center_z))

    fragile_cells = []

    for r in range(len(matrix)):
        for c in range(len(matrix[0])):
            val = matrix[r][c]
            if val == VOID:
                continue

            if val == BRIDGE:
                is_open = (r, c) in game.open_bridges
                ent = Entity(model='cube', color=color.green, texture='brick',
                              position=(c, 0, r), scale=(0.95, 0.2, 0.95),
                              enabled=is_open)
                tile_entities[(r, c)] = ent
                continue

            base_color = color.cyan
            y, h = 0, 0.2
            if val == GOAL:
                base_color, y, h = color.red, -0.05, 0.1
            elif val == FRAGILE:
                base_color = color.orange
                fragile_cells.append((r, c))

            base = Entity(model='cube', color=base_color, texture='brick',
                          position=(c, y, r), scale=(0.95, h, 0.95))
            tile_entities[(r, c)] = base

            try:
                if val == SOFT_SWITCH:
                    Entity(parent=base, model='circle', color=color.azure,
                           rotation_x=90, position=(0, 0.55, 0), scale=0.6)
                elif val == HEAVY_SWITCH:
                    Entity(parent=base, model='cube', color=color.violet,
                           rotation=(90, 0, 45), position=(0, 0.55, 0), scale=(0.08, 0.75, 0.75))
                    Entity(parent=base, model='cube', color=color.violet,
                           rotation=(90, 0, -45), position=(0, 0.55, 0), scale=(0.08, 0.75, 0.75))
                elif val == SPLIT_SWITCH:
                    Text(text='( )', parent=base, position=(0, 0.6, 0),
                         scale=30, origin=(0, 0), color=color.yellow, rotation_x=90)
            except Exception:
                if val == SOFT_SWITCH:
                    base.color = color.azure
                elif val == HEAVY_SWITCH:
                    base.color = color.violet
                elif val == SPLIT_SWITCH:
                    base.color = color.magenta

    block = Entity(model='cube', color=color.white, texture='brick')
    cube_a = Entity(model='cube', color=color.white, texture='brick', scale=(0.9, 0.9, 0.9), enabled=False)
    cube_b = Entity(model='cube', color=color.white, texture='brick', scale=(0.9, 0.9, 0.9), enabled=False)

    reset_game()

ACTIVE_CUBE_COLOR = color.yellow
INACTIVE_CUBE_COLOR = color.white.tint(-.3)

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

def refresh_bridge_colors():
    for (r, c), ent in tile_entities.items():
        if board.grid[r][c] == BRIDGE:
            ent.enabled = (r, c) in game.open_bridges

def break_fragile_if_needed(status):
    if status != "LOSE_FALL" or game.orientation != 'STANDING':
        return
    pos = (game.r, game.c)
    if pos in tile_entities and board.tile_at(*pos) == FRAGILE:
        tile_entities[pos].enabled = False

def restore_fragile_tiles():
    for pos in fragile_cells:
        if pos in tile_entities:
            tile_entities[pos].enabled = True

def reset_game():
    global game_over, is_falling, fall_speed, delay_timer, is_solving, solve_queue, solve_step_timer
    game.r, game.c, game.orientation = start_row, start_col, 'STANDING'
    game.open_bridges = set(board.initial_open_bridges)
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
    restore_fragile_tiles()
    update_block_visuals()
    refresh_bridge_colors()
    if status_text:
        status_text.text = "Di chuyển: W, A, S, D | Reset: R | Đổi cube: Space (khi split)"
    if solve_info_text:
        solve_info_text.text = ""
    if stats_text:
        stats_text.text = ""

def run_algorithm(name, solve_fn):
    global is_solving, solve_queue

    reset_game()
    solve_info_text.text = f"Đang tính {name}..."

    tracemalloc.start()
    t0 = pytime.perf_counter()
    try:
        path, nodes_expanded = solve_fn(board, start_row, start_col)
    except Exception as e:
        tracemalloc.stop()
        solve_info_text.text = f"<red>{name} lỗi: {e}"
        return
    elapsed = pytime.perf_counter() - t0
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if not path:
        solve_info_text.text = f"<red>{name}: không tìm được lời giải."
        stats_text.text = f"Thời gian: {elapsed:.4f}s | Bộ nhớ đỉnh: {peak_mem/1024:.1f} KB | Node mở rộng: {nodes_expanded}"
        return

    solve_info_text.text = f"<green>{name}: đang phát lại {len(path)} bước..."
    stats_text.text = (f"Thời gian: {elapsed:.4f}s | Bộ nhớ đỉnh: {peak_mem/1024:.1f} KB | "
                        f"Node mở rộng: {nodes_expanded} | Số bước: {len(path)}")
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

def on_load_stage():
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        path = filedialog.askopenfilename(
            initialdir=STAGES_DIR, title="Chọn file stage",
            filetypes=[("Stage files", "*.txt")])
        root.destroy()
    except Exception as e:
        if solve_info_text:
            solve_info_text.text = f"<red>Không mở được hộp thoại chọn file: {e}"
        return

    if path:
        build_level(path)

btn_bfs = Button(text='Solve BFS', color=color.azure, scale=(0.15, 0.05), position=(0.62, 0.45), on_click=on_solve_bfs)
btn_dfs = Button(text='Solve DFS', color=color.azure, scale=(0.15, 0.05), position=(0.62, 0.38), on_click=on_solve_dfs)
btn_ucs = Button(text='Solve UCS', color=color.azure, scale=(0.15, 0.05), position=(0.62, 0.31), on_click=on_solve_ucs)
btn_astar = Button(text='Solve A*', color=color.azure, scale=(0.15, 0.05), position=(0.62, 0.24), on_click=on_solve_astar)
btn_load = Button(text='Load Stage', color=color.orange, scale=(0.15, 0.05), position=(0.62, 0.17), on_click=on_load_stage)
btn_reset = Button(text='Reset', color=color.red.tint(-.2), scale=(0.15, 0.05), position=(0.62, 0.10), on_click=reset_game)

status_text = Text(text="", position=(-0.85, 0.45), scale=1.1, color=color.white)
solve_info_text = Text(text="", position=(-0.85, 0.40), scale=1.0, color=color.yellow)
stats_text = Text(text="", position=(-0.85, 0.35), scale=0.9, color=color.lime)

build_level(DEFAULT_STAGE)

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

    if is_solving and not game_over:
        solve_step_timer -= time.dt
        if solve_step_timer <= 0:
            solve_step_timer = SOLVE_STEP_INTERVAL
            if solve_queue:
                action = solve_queue.pop(0)
                status = game.move(action)
                update_block_visuals()
                refresh_bridge_colors()
                break_fragile_if_needed(status)
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
        return

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
    break_fragile_if_needed(status)

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
