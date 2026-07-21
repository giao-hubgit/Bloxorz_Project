from collections import deque
from typing import Tuple, Optional, List
from core.state import State, successors, Board


def solve(board: Board, start_r: int, start_c: int) -> Tuple[Optional[List[str]], int]:
    """Tìm kiếm theo chiều rộng (BFS). Trả về (path, nodes_expanded).

    `board` chứa grid + switch/bridge (xem core/state.py). State ban đầu
    lấy open_bridges = board.initial_open_bridges để đảm bảo màn chơi có
    cầu mở sẵn (INIT ... OPEN) được xử lý đúng ngay từ đầu.
    """
    start = State(start_r, start_c, 'STANDING', board.initial_open_bridges)
    q = deque([start])
    parent = {start: None}
    parent_action = {}
    visited = {start}
    nodes_expanded = 0

    while q:
        cur = q.popleft()
        nodes_expanded += 1
        for action, nxt, status in successors(cur, board):
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = cur
            parent_action[nxt] = action
            if status == 'WIN':
                path = [action]
                p = cur
                while parent[p] is not None:
                    path.append(parent_action[p])
                    p = parent[p]
                path.reverse()
                return path, nodes_expanded
            if status == 'CONTINUE':
                q.append(nxt)
    return None, nodes_expanded
