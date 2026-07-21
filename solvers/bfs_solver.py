from collections import deque
from typing import List, Tuple, Optional
from core.state import State, successors


def solve(grid: List[List[int]], start_r: int, start_c: int) -> Tuple[Optional[List[str]], int]:
    #Tìm kiếm theo chiều rộng (BFS). Trả về (path, nodes_expanded).
    #Sử dụng State để hash nhằm tránh thăm lại các trạng thái.
    
    start = State(start_r, start_c, 'STANDING')
    q = deque([start])
    parent = {start: None}
    parent_action = {}
    visited = {start}
    nodes_expanded = 0

    while q:
        cur = q.popleft()
        nodes_expanded += 1
        for action, nxt, status in successors(cur, grid):
            if nxt in visited:
                continue
            visited.add(nxt)
            parent[nxt] = cur
            parent_action[nxt] = action
            if status == 'WIN':
                # reconstruct path
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
