from typing import List, Tuple, Optional, Set
from core.state import State, successors


def depth_limited_dfs(grid, start: State, limit: int):
    nodes = 0

    def dfs(node: State, depth: int, visited: Set[State]):
        nonlocal nodes
        nodes += 1
        if depth == 0:
            return None
        for action, nxt, status in successors(node, grid):
            if nxt in visited:
                continue
            if status == 'WIN':
                return [action]
            visited.add(nxt)
            res = dfs(nxt, depth - 1, visited)
            visited.remove(nxt)
            if res is not None:
                return [action] + res
        return None

    visited = {start}
    return dfs(start, limit, visited), nodes


def ids(grid: List[List[int]], start_r: int, start_c: int, max_depth: int = 200) -> Tuple[Optional[List[str]], int]:
    #DFS tăng dần (IDS). Đảm bảo xử lý trạng thái lặp bằng cách dùng tập `visited` trong mỗi lần tìm có giới hạn độ sâu.
    start = State(start_r, start_c, 'STANDING')
    total_nodes = 0
    for depth in range(1, max_depth + 1):
        path, nodes = depth_limited_dfs(grid, start, depth)
        total_nodes += nodes
        if path is not None:
            return path, total_nodes
    return None, total_nodes
