import heapq
import itertools
from typing import Tuple, Optional, List
from core.state import State, successors, Board, GOAL


def find_goal(board: Board) -> Tuple[int, int]:
    for r in range(board.rows):
        for c in range(board.cols):
            if board.grid[r][c] == GOAL:
                return r, c
    return -1, -1


def heuristic(state: State, goal_r: int, goal_c: int) -> float:
    if goal_r == -1 or goal_c == -1:
        return 0.0

    if state.is_split:
        dist1 = (abs(state.cube1[0] - goal_r) + abs(state.cube1[1] - goal_c)) if state.cube1 else 9999
        dist2 = (abs(state.cube2[0] - goal_r) + abs(state.cube2[1] - goal_c)) if state.cube2 else 9999
        return (min(dist1, dist2) / 2.0) + 1.0

    manhattan_dist = abs(state.r - goal_r) + abs(state.c - goal_c)
    h = manhattan_dist / 2.0

    if state.orientation != 'STANDING':
        h += 0.5

    return h


def solve(board: Board, start_r: int, start_c: int) -> Tuple[Optional[List[str]], int]:
    goal_r, goal_c = find_goal(board)
    start = State(start_r, start_c, 'STANDING', board.initial_open_bridges)

    pq = []
    counter = itertools.count()
    start_h = heuristic(start, goal_r, goal_c)
    heapq.heappush(pq, (start_h, next(counter), 0, start))

    g_score = {start: 0}
    parent = {start: None}
    parent_action = {}
    nodes_expanded = 0

    while pq:
        f, _, g, cur = heapq.heappop(pq)

        if g > g_score.get(cur, float('inf')):
            continue

        nodes_expanded += 1

        for action, nxt, status in successors(cur, board):
            new_g = g + 1

            if status == 'WIN':
                parent[nxt] = cur
                parent_action[nxt] = action

                path = []
                p = nxt
                while parent[p] is not None:
                    path.append(parent_action[p])
                    p = parent[p]
                path.reverse()
                return path, nodes_expanded

            if status == 'CONTINUE':
                if nxt not in g_score or new_g < g_score[nxt]:
                    g_score[nxt] = new_g
                    parent[nxt] = cur
                    parent_action[nxt] = action

                    new_h = heuristic(nxt, goal_r, goal_c)
                    new_f = new_g + new_h
                    heapq.heappush(pq, (new_f, next(counter), new_g, nxt))

    return None, nodes_expanded