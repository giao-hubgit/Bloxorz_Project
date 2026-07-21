import tracemalloc
import time
from solvers import bfs_solver, dfs_solver, ucs_solver
from core.state import State
from typing import List, Tuple


def run_solver(func, grid, start_r, start_c):
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(grid, start_r, start_c)
    t1 = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    if isinstance(result, tuple):
        path, nodes = result
    else:
        path, nodes = result, 0
    return {
        'time_s': t1 - t0,
        'peak_memory_bytes': peak,
        'nodes_expanded': nodes,
        'path_length': len(path) if path else 0
    }


def make_grid(rows, cols, holes=0):
    # lưới đơn giản: ô có giá trị 1 là ô đi được, ô đích đặt ở góc phải dưới (2)
    grid = [[1 for _ in range(cols)] for __ in range(rows)]
    grid[rows - 1][cols - 1] = 2
    import random
    for _ in range(holes):
        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)
        if (r, c) not in [(0, 0), (rows - 1, cols - 1)]:
            grid[r][c] = 0
    return grid


def main():
    tests = []
    # tạo 10 test grid tăng dần kích thước/độ khó
    tests.append((make_grid(3, 3, holes=0), 0, 0))
    tests.append((make_grid(4, 4, holes=1), 0, 0))
    tests.append((make_grid(5, 5, holes=2), 0, 0))
    tests.append((make_grid(5, 6, holes=3), 0, 0))
    tests.append((make_grid(6, 6, holes=4), 0, 0))
    tests.append((make_grid(7, 7, holes=6), 0, 0))
    tests.append((make_grid(7, 8, holes=8), 0, 0))
    tests.append((make_grid(8, 8, holes=10), 0, 0))
    tests.append((make_grid(9, 9, holes=12), 0, 0))
    tests.append((make_grid(10, 10, holes=15), 0, 0))

    solvers = [
        ('BFS', bfs_solver.solve),
        ('IDS', dfs_solver.ids),
        ('UCS', ucs_solver.solve),
    ]

    for i, (grid, sr, sc) in enumerate(tests, start=1):
        print(f"Test {i}: size={len(grid)}x{len(grid[0])}")
        for name, func in solvers:
            metrics = run_solver(func, grid, sr, sc)
            print(f"  {name}: time={metrics['time_s']:.6f}s, peak_mem={metrics['peak_memory_bytes']} bytes, nodes={metrics['nodes_expanded']}, path_len={metrics['path_length']}")


if __name__ == '__main__':
    main()
