
from dataclasses import dataclass, field
from typing import FrozenSet, Tuple, List, Iterable, Dict, Optional

VOID = 0
FLOOR = 1
GOAL = 2
FRAGILE = 3
BRIDGE = 4
SOFT_SWITCH = 5
HEAVY_SWITCH = 6
SPLIT_SWITCH = 7

@dataclass(frozen=True)
class Switch:
    r: int
    c: int
    kind: str
    mode: str
    group: str
    target_open: Optional[bool] = None

@dataclass(frozen=True)
class SplitSwitchDecl:
    r: int
    c: int
    target_a: Tuple[int, int]
    target_b: Tuple[int, int]

@dataclass
class Board:
    grid: List[List[int]]
    switches: List[Switch] = field(default_factory=list)
    bridge_groups: Dict[str, Tuple[Tuple[int, int], ...]] = field(default_factory=dict)
    initial_open_bridges: FrozenSet[Tuple[int, int]] = frozenset()
    split_switches: List[SplitSwitchDecl] = field(default_factory=list)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    def tile_at(self, r: int, c: int) -> int:
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return VOID
        return self.grid[r][c]

@dataclass(frozen=True)
class State:
    r: int
    c: int
    orientation: str
    open_bridges: FrozenSet[Tuple[int, int]] = frozenset()

    def occupied_cells(self) -> Tuple[Tuple[int, int], ...]:
        if self.orientation == 'STANDING':
            return ((self.r, self.c),)
        elif self.orientation == 'LYING_H':
            return ((self.r, self.c), (self.r, self.c + 1))
        elif self.orientation == 'LYING_V':
            return ((self.r, self.c), (self.r + 1, self.c))
        else:
            raise ValueError('Invalid orientation')

def _is_passable(board: Board, r: int, c: int, open_bridges: FrozenSet[Tuple[int, int]]) -> bool:
    tile = board.tile_at(r, c)
    if tile == VOID:
        return False
    if tile == BRIDGE:
        return (r, c) in open_bridges
    return True

def check_state_status(state: State, board: Board) -> str:
    cells = state.occupied_cells()

    for (pr, pc) in cells:
        if not _is_passable(board, pr, pc, state.open_bridges):
            return 'LOSE_FALL'

    if state.orientation == 'STANDING':
        r, c = cells[0]
        if board.tile_at(r, c) == FRAGILE:
            return 'LOSE_FALL'

    if state.orientation == 'STANDING' and board.tile_at(state.r, state.c) == GOAL:
        return 'WIN'

    return 'CONTINUE'

def _apply_switches(board: Board, cells: Tuple[Tuple[int, int], ...], orientation: str,
                     open_bridges: FrozenSet[Tuple[int, int]]) -> FrozenSet[Tuple[int, int]]:
    new_open = set(open_bridges)
    cell_set = set(cells)

    for sw in board.switches:
        if (sw.r, sw.c) not in cell_set:
            continue

        if sw.kind == 'SOFT':
            triggered = True
        elif sw.kind == 'HEAVY':
            triggered = (orientation == 'STANDING' and len(cells) == 1 and cells[0] == (sw.r, sw.c))
        else:
            triggered = False

        if not triggered:
            continue

        group_cells = board.bridge_groups.get(sw.group, ())

        if sw.mode == 'TOGGLE':
            for cell in group_cells:
                if cell in new_open:
                    new_open.discard(cell)
                else:
                    new_open.add(cell)
        elif sw.mode == 'PERMANENT':
            for cell in group_cells:
                if sw.target_open:
                    new_open.add(cell)
                else:
                    new_open.discard(cell)

    return frozenset(new_open)

def move_state(state: State, direction: str) -> State:
    r, c = state.r, state.c
    ori = state.orientation
    ob = state.open_bridges
    if ori == 'STANDING':
        if direction == 'LEFT':
            return State(r, c - 2, 'LYING_H', ob)
        elif direction == 'RIGHT':
            return State(r, c + 1, 'LYING_H', ob)
        elif direction == 'UP':
            return State(r - 2, c, 'LYING_V', ob)
        elif direction == 'DOWN':
            return State(r + 1, c, 'LYING_V', ob)
    elif ori == 'LYING_H':
        if direction == 'LEFT':
            return State(r, c - 1, 'STANDING', ob)
        elif direction == 'RIGHT':
            return State(r, c + 2, 'STANDING', ob)
        elif direction == 'UP':
            return State(r - 1, c, 'LYING_H', ob)
        elif direction == 'DOWN':
            return State(r + 1, c, 'LYING_H', ob)
    elif ori == 'LYING_V':
        if direction == 'LEFT':
            return State(r, c - 1, 'LYING_V', ob)
        elif direction == 'RIGHT':
            return State(r, c + 1, 'LYING_V', ob)
        elif direction == 'UP':
            return State(r - 1, c, 'STANDING', ob)
        elif direction == 'DOWN':
            return State(r + 2, c, 'STANDING', ob)
    raise ValueError('Invalid move')

def successors(state: State, board: Board) -> Iterable[Tuple[str, State, str]]:
    for action in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
        try:
            moved = move_state(state, action)
        except ValueError:
            continue

        cells = moved.occupied_cells()
        new_open = _apply_switches(board, cells, moved.orientation, moved.open_bridges)
        new_state = State(moved.r, moved.c, moved.orientation, new_open)

        status = check_state_status(new_state, board)
        yield action, new_state, status
