from dataclasses import dataclass
from typing import FrozenSet, Tuple, List, Iterable

@dataclass(frozen=True)
class State:
    r: int
    c: int
    orientation: str  # 'STANDING', 'LYING_H', 'LYING_V'
    bridges: FrozenSet[Tuple[int,int]] = frozenset()

    def occupied_cells(self) -> Tuple[Tuple[int,int], ...]:
        if self.orientation == 'STANDING':
            return ((self.r, self.c),)
        elif self.orientation == 'LYING_H':
            return ((self.r, self.c), (self.r, self.c + 1))
        elif self.orientation == 'LYING_V':
            return ((self.r, self.c), (self.r + 1, self.c))
        else:
            raise ValueError('Invalid orientation')


def check_state_status(state: State, grid: List[List[int]]) -> str:
    rows = len(grid)
    cols = len(grid[0])
    cells = state.occupied_cells()
    void_cells = []
    for pr, pc in cells:
        is_void = False
        if pr < 0 or pr >= rows or pc < 0 or pc >= cols:
            is_void = True
        elif grid[pr][pc] == 0:
            is_void = True
        if is_void:
            void_cells.append((pr, pc))

    if void_cells:
        return 'LOSE_FALL'

    if state.orientation == 'STANDING' and grid[state.r][state.c] == 2:
        return 'WIN'
    return 'CONTINUE'


def move_state(state: State, direction: str) -> State:
    r, c = state.r, state.c
    ori = state.orientation
    if ori == 'STANDING':
        if direction == 'LEFT':
            return State(r, c - 2, 'LYING_H', state.bridges)
        elif direction == 'RIGHT':
            return State(r, c + 1, 'LYING_H', state.bridges)
        elif direction == 'UP':
            return State(r - 2, c, 'LYING_V', state.bridges)
        elif direction == 'DOWN':
            return State(r + 1, c, 'LYING_V', state.bridges)
    elif ori == 'LYING_H':
        if direction == 'LEFT':
            return State(r, c - 1, 'STANDING', state.bridges)
        elif direction == 'RIGHT':
            return State(r, c + 2, 'STANDING', state.bridges)
        elif direction == 'UP':
            return State(r - 1, c, 'LYING_H', state.bridges)
        elif direction == 'DOWN':
            return State(r + 1, c, 'LYING_H', state.bridges)
    elif ori == 'LYING_V':
        if direction == 'LEFT':
            return State(r, c - 1, 'LYING_V', state.bridges)
        elif direction == 'RIGHT':
            return State(r, c + 1, 'LYING_V', state.bridges)
        elif direction == 'UP':
            return State(r - 1, c, 'STANDING', state.bridges)
        elif direction == 'DOWN':
            return State(r + 2, c, 'STANDING', state.bridges)
    raise ValueError('Invalid move')


def successors(state: State, grid: List[List[int]]) -> Iterable[Tuple[str, State, str]]:
    for action in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
        try:
            new_state = move_state(state, action)
        except ValueError:
            continue
        status = check_state_status(new_state, grid)
        yield action, new_state, status
