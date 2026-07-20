import heapq
import itertools
from typing import List, Tuple, Optional
from core.state import State, successors


def move_cost(new_state: State) -> int:
    """Thiết kế hàm chi phí:
    - Nếu sau bước di chuyển block ở trạng thái `STANDING` thì chi phí = 1.
    - Nếu ở `LYING_H` hoặc `LYING_V` thì chi phí = 2.

    Lý giải: trạng thái nằm (lying) chạm hai ô cùng lúc (diện tích lớn hơn),
    nên xem là tốn công hơn -> gán chi phí 2. Trạng thái đứng chiếm một ô nên chi phí 1.
    Việc này tạo chi phí không đồng nhất để UCS có thể khác với BFS.
    """
    if new_state.orientation == 'STANDING':
        return 1
    return 2


def solve(grid: List[List[int]], start_r: int, start_c: int) -> Tuple[Optional[List[str]], int]:
    start = State(start_r, start_c, 'STANDING')
    pq = []  # (cost, counter, state)
    counter = itertools.count()
    heapq.heappush(pq, (0, next(counter), start))
    dist = {start: 0}
    parent = {start: None}
    parent_action = {}
    nodes_expanded = 0

    while pq:
        cost, _, cur = heapq.heappop(pq)
        if cost != dist.get(cur, float('inf')):
            continue
        nodes_expanded += 1
        for action, nxt, status in successors(cur, grid):
            step = move_cost(nxt)
            new_cost = cost + step
            if nxt not in dist or new_cost < dist[nxt]:
                dist[nxt] = new_cost
                parent[nxt] = cur
                parent_action[nxt] = action
                if status == 'WIN':
                    # reconstruct path
                    # xây dựng lại đường đi
                    path = [action]
                    p = cur
                    while parent[p] is not None:
                        path.append(parent_action[p])
                        p = parent[p]
                    path.reverse()
                    return path, nodes_expanded
                if status == 'CONTINUE':
                    heapq.heappush(pq, (new_cost, next(counter), nxt))
    return None, nodes_expanded
