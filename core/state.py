"""
core/state.py

State representation dùng chung cho GUI (thông qua BloxorzCore) và toàn bộ
solver (BFS/DFS/UCS/A*).

Mở rộng so với bản gốc: hỗ trợ fragile tile, bridge, soft switch, heavy switch.

Loại ô trên `grid` (số nguyên):
    0 = VOID            ô trống, không có gạch
    1 = FLOOR            sàn thường
    2 = GOAL              đích
    3 = FRAGILE           gạch dễ vỡ (chỉ chịu được khi khối NẰM)
    4 = BRIDGE            cầu (đóng = như VOID, mở = như FLOOR)
    5 = SOFT_SWITCH       công tắc mềm (kích hoạt dù đứng hay nằm)
    6 = HEAVY_SWITCH      công tắc nặng (chỉ kích hoạt khi khối ĐỨNG)

`Board` chứa dữ liệu TĨNH của màn chơi (grid + danh sách switch).
`State` chứa dữ liệu ĐỘNG cần cho search: vị trí, hướng khối, và tập các ô
bridge đang MỞ (open_bridges) — vì đề yêu cầu 2 state có cùng vị trí/hướng
khối nhưng khác cấu hình cầu phải được xem là 2 state khác nhau.
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Tuple, List, Iterable, Dict, Optional

# ---- Hằng số loại ô ----
VOID = 0
FLOOR = 1
GOAL = 2
FRAGILE = 3
BRIDGE = 4
SOFT_SWITCH = 5
HEAVY_SWITCH = 6
SPLIT_SWITCH = 7

# LƯU Ý PHẠM VI: Split switch (tách khối thành 2 cube 1x1x1) hiện chỉ được
# cài đặt cho GUI/chơi tay (BloxorzCore), KHÔNG có trong State/successors()
# dùng cho BFS/DFS/UCS/A*. Việc mở rộng không gian trạng thái để solver
# hiểu được "split mode" (2 cube độc lập + cube nào đang active) là một
# phần việc lớn hơn hẳn — chưa làm ở đây, cần bàn thêm với nhóm nếu muốn
# solver cũng xử lý được split switch.


@dataclass(frozen=True)
class Switch:
    r: int
    c: int
    kind: str            # 'SOFT' | 'HEAVY'
    mode: str             # 'TOGGLE' | 'PERMANENT'
    group: str            # tên nhóm bridge mà switch này điều khiển
    target_open: Optional[bool] = None  # chỉ dùng khi mode == 'PERMANENT'


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
    orientation: str  # 'STANDING', 'LYING_H', 'LYING_V'
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
    """Ô có thể đứng/nằm lên được không (chưa xét fragile khi đứng)."""
    tile = board.tile_at(r, c)
    if tile == VOID:
        return False
    if tile == BRIDGE:
        return (r, c) in open_bridges
    # FLOOR, GOAL, FRAGILE, SOFT_SWITCH, HEAVY_SWITCH đều "có gạch" để đi qua/nằm lên
    return True


def check_state_status(state: State, board: Board) -> str:
    """Trả về 'WIN' | 'LOSE_FALL' | 'CONTINUE'."""
    cells = state.occupied_cells()

    for (pr, pc) in cells:
        if not _is_passable(board, pr, pc, state.open_bridges):
            return 'LOSE_FALL'

    # Fragile tile: đứng lên là vỡ (dù ô đó chịu tải được như floor khi nằm)
    if state.orientation == 'STANDING':
        r, c = cells[0]
        if board.tile_at(r, c) == FRAGILE:
            return 'LOSE_FALL'

    if state.orientation == 'STANDING' and board.tile_at(state.r, state.c) == GOAL:
        return 'WIN'

    return 'CONTINUE'


def _apply_switches(board: Board, cells: Tuple[Tuple[int, int], ...], orientation: str,
                     open_bridges: FrozenSet[Tuple[int, int]]) -> FrozenSet[Tuple[int, int]]:
    """Cập nhật open_bridges dựa trên switch mà khối vừa chạm/đứng lên."""
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
    """Sinh (action, new_state, status) cho 4 hướng đi.

    Lưu ý: open_bridges của new_state đã được cập nhật theo switch (nếu có)
    TRƯỚC khi tính status, vì việc kích hoạt switch xảy ra ngay khi khối
    chạm/đứng lên nó, và có thể quyết định ô tiếp theo có sập hay không
    (ví dụ: đứng lên soft switch mở luôn cây cầu ngay dưới chân).
    """
    for action in ('LEFT', 'RIGHT', 'UP', 'DOWN'):
        try:
            moved = move_state(state, action)
        except ValueError:
            continue

        cells = moved.occupied_cells()
        # Chỉ áp dụng switch nếu khối thực sự đứng trên nền vững (không rơi
        # ngay tại các ô không phải switch); ta vẫn cho áp dụng switch trước
        # rồi mới check status, vì switch có thể MỞ cầu đang đứng lên.
        new_open = _apply_switches(board, cells, moved.orientation, moved.open_bridges)
        new_state = State(moved.r, moved.c, moved.orientation, new_open)

        status = check_state_status(new_state, board)
        yield action, new_state, status
