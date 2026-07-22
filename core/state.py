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

    is_split: bool = False
    cube1: Optional[Tuple[int, int]] = None 
    cube2: Optional[Tuple[int, int]] = None  
    active_cube: int = 0                     

    def occupied_cells(self) -> Tuple[Tuple[int, int], ...]:
        if self.is_split:
            res = []
            if self.cube1: res.append(self.cube1)
            if self.cube2: res.append(self.cube2)
            return tuple(res)
        if self.orientation == 'STANDING':
            return ((self.r, self.c),)
        elif self.orientation == 'LYING_H':
            return ((self.r, self.c), (self.r, self.c + 1))
        elif self.orientation == 'LYING_V':
            return ((self.r, self.c), (self.r + 1, self.c))
        else:
            raise ValueError(f'Invalid orientation: {self.orientation}')

def _is_passable(board: Board, r: int, c: int, open_bridges: FrozenSet[Tuple[int, int]]) -> bool:
    tile = board.tile_at(r, c)
    if tile == VOID:
        return False
    if tile == BRIDGE:
        return (r, c) in open_bridges
    return True

def check_state_status(state: State, board: Board) -> str:
    if state.is_split:
        if state.cube1 is None or state.cube2 is None:
            return 'LOSE_FALL'
        if not _is_passable(board, state.cube1[0], state.cube1[1], state.open_bridges):
            return 'LOSE_FALL'
        if not _is_passable(board, state.cube2[0], state.cube2[1], state.open_bridges):
            return 'LOSE_FALL'
        return 'CONTINUE'

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
                     open_bridges: FrozenSet[Tuple[int, int]], is_split: bool = False) -> FrozenSet[Tuple[int, int]]:
    new_open = set(open_bridges)
    cell_set = set(cells)

    for sw in board.switches:
        if (sw.r, sw.c) not in cell_set:
            continue

        if is_split:
            triggered = (sw.kind == 'SOFT')
        else:
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
    if state.is_split:
        if direction == 'SWITCH_CUBE':
            return State(
                r=state.r, c=state.c, orientation='SPLIT',
                open_bridges=state.open_bridges,
                is_split=True, cube1=state.cube1, cube2=state.cube2,
                active_cube=1 - state.active_cube
            )

        dr, dc = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}[direction]
        active_pos = state.cube1 if state.active_cube == 0 else state.cube2
        if active_pos is None:
            raise ValueError("Cube position is missing")
            
        new_r, new_c = active_pos[0] + dr, active_pos[1] + dc

        c1 = (new_r, new_c) if state.active_cube == 0 else state.cube1
        c2 = (new_r, new_c) if state.active_cube == 1 else state.cube2

        if c1 and c2:
            if c1[0] == c2[0] and abs(c1[1] - c2[1]) == 1:
                left = c1 if c1[1] < c2[1] else c2
                return State(r=left[0], c=left[1], orientation='LYING_H', open_bridges=state.open_bridges, is_split=False)
            elif c1[1] == c2[1] and abs(c1[0] - c2[0]) == 1:
                top = c1 if c1[0] < c2[0] else c2
                return State(r=top[0], c=top[1], orientation='LYING_V', open_bridges=state.open_bridges, is_split=False)

        return State(
            r=0, c=0, orientation='SPLIT',
            open_bridges=state.open_bridges,
            is_split=True, cube1=c1, cube2=c2, active_cube=state.active_cube
        )

    r, c = state.r, state.c
    ori = state.orientation
    ob = state.open_bridges
    if ori == 'STANDING':
        if direction == 'LEFT': return State(r, c - 2, 'LYING_H', ob)
        elif direction == 'RIGHT': return State(r, c + 1, 'LYING_H', ob)
        elif direction == 'UP': return State(r - 2, c, 'LYING_V', ob)
        elif direction == 'DOWN': return State(r + 1, c, 'LYING_V', ob)
    elif ori == 'LYING_H':
        if direction == 'LEFT': return State(r, c - 1, 'STANDING', ob)
        elif direction == 'RIGHT': return State(r, c + 2, 'STANDING', ob)
        elif direction == 'UP': return State(r - 1, c, 'LYING_H', ob)
        elif direction == 'DOWN': return State(r + 1, c, 'LYING_H', ob)
    elif ori == 'LYING_V':
        if direction == 'LEFT': return State(r, c - 1, 'LYING_V', ob)
        elif direction == 'RIGHT': return State(r, c + 1, 'LYING_V', ob)
        elif direction == 'UP': return State(r - 1, c, 'STANDING', ob)
        elif direction == 'DOWN': return State(r + 2, c, 'STANDING', ob)
        
    raise ValueError('Invalid move')

def successors(state: State, board: Board) -> Iterable[Tuple[str, State, str]]:
    if state.is_split:
        actions = ('LEFT', 'RIGHT', 'UP', 'DOWN', 'SWITCH_CUBE')
        for action in actions:
            if action == 'SWITCH_CUBE':
                nxt = move_state(state, 'SWITCH_CUBE')
                status = check_state_status(nxt, board)
                yield action, nxt, status
            else:
                try:
                    moved = move_state(state, action)
                except (ValueError, KeyError):
                    continue

                if moved.is_split:
                    active_pos = moved.cube1 if moved.active_cube == 0 else moved.cube2
                    if active_pos:
                        new_open = _apply_switches(board, (active_pos,), 'SPLIT', moved.open_bridges, is_split=True)
                        new_state = State(
                            r=moved.r, c=moved.c, orientation=moved.orientation,
                            open_bridges=new_open, is_split=True,
                            cube1=moved.cube1, cube2=moved.cube2, active_cube=moved.active_cube
                        )
                    else:
                        new_state = moved
                else:
                    cells = moved.occupied_cells()
                    new_open = _apply_switches(board, cells, moved.orientation, moved.open_bridges, is_split=False)
                    new_state = State(
                        r=moved.r, c=moved.c, orientation=moved.orientation,
                        open_bridges=new_open, is_split=False
                    )

                status = check_state_status(new_state, board)
                yield action, new_state, status
    else:
        for action in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
            try:
                moved = move_state(state, action)
            except (ValueError, KeyError):
                continue

            cells = moved.occupied_cells()
            new_open = _apply_switches(board, cells, moved.orientation, moved.open_bridges, is_split=False)

            is_split_now = False
            cube1, cube2 = None, None
            if moved.orientation == 'STANDING':
                for sp in board.split_switches:
                    if (sp.r, sp.c) == (moved.r, moved.c):
                        is_split_now = True
                        cube1 = sp.target_a
                        cube2 = sp.target_b
                        break

            if is_split_now:
                new_state = State(
                    r=0, c=0, orientation='SPLIT',
                    open_bridges=new_open,
                    is_split=True, cube1=cube1, cube2=cube2, active_cube=0
                )
            else:
                new_state = State(
                    r=moved.r, c=moved.c, orientation=moved.orientation,
                    open_bridges=new_open
                )

            status = check_state_status(new_state, board)
            yield action, new_state, status