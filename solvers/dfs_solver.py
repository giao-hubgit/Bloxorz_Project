from typing import Tuple, Optional, Set, List
from core.state import State, successors, Board


def depth_limited_dfs(board: Board, start: State, limit: int):
    nodes = 0

    def dfs(node: State, depth: int, visited: Set[State]):
        nonlocal nodes
        nodes += 1
        if depth == 0:
            return None
        for action, nxt, status in successors(node, board):
            if nxt in visited:
                continue
            if status == 'WIN':
                return [action]
            if status != 'CONTINUE':
                continue
            visited.add(nxt)
            res = dfs(nxt, depth - 1, visited)
            if res is not None:
                return [action] + res
        return None

    visited = {start}
    return dfs(start, limit, visited), nodes


def ids(board: Board, start_r: int, start_c: int, max_depth: int = 200) -> Tuple[Optional[List[str]], int]:
    start = State(start_r, start_c, 'STANDING', board.initial_open_bridges)
    total_nodes = 0
    for depth in range(1, max_depth + 1):
        path, nodes = depth_limited_dfs(board, start, depth)
        total_nodes += nodes
        if path is not None:
            return path, total_nodes
    return None, total_nodes
