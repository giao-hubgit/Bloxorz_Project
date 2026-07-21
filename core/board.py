"""
core/board.py

Đọc file stage (.txt) thành Board (xem core/state.py).

*** LƯU Ý: đây là bản NHÁP để test logic fragile/bridge/switch. Phần hoàn
thiện chính thức của map loader (bao gồm chọn lại/định dạng lại token nếu
cần) sẽ do bạn phụ trách A* thực hiện — bản này chỉ để tham khảo và chạy
thử nghiệm cho tới lúc đó. ***

ĐỊNH DẠNG FILE:

  Phần 1 — lưới (bắt buộc), mỗi ô cách nhau bởi khoảng trắng:
    0 = void        1 = floor        2 = goal        S = start (floor)
    3 = fragile     4 = bridge       5 = soft switch  6 = heavy switch

  Phần 2 — khai báo switch/bridge (tùy chọn), sau một dòng trống:
    BRIDGE <group> <r1> <c1> <r2> <c2> ...
        Khai báo các ô thuộc nhóm cầu <group>. Có thể khai nhiều dòng
        BRIDGE cùng group để gộp lại.

    SWITCH <r> <c> <SOFT|HEAVY> <TOGGLE|PERMANENT> <group> [OPEN|CLOSED]
        Khai báo switch tại (r, c), loại, chế độ, nhóm cầu nó điều khiển.
        [OPEN|CLOSED] chỉ bắt buộc khi mode = PERMANENT (trạng thái cầu
        sau khi switch được kích hoạt).

    INIT <group> <OPEN|CLOSED>
        (tùy chọn) trạng thái ban đầu của nhóm cầu, mặc định là CLOSED.

    SPLIT <r> <c> <target_a_r> <target_a_c> <target_b_r> <target_b_c>
        Khai báo split switch tại (r, c) — token 7 trên lưới. Khi khối ĐỨNG
        lên đúng ô này, nó tách thành 2 cube 1x1x1, dịch chuyển tới 2 vị trí
        target_a / target_b. (Chỉ dùng cho GUI/chơi tay — xem state.py.)

VÍ DỤ:
    1 1 1 0 0
    1 S 1 4 2
    1 1 1 0 0

    BRIDGE b1 1 3
    SWITCH 0 0 SOFT TOGGLE b1
"""

from core.state import Board, Switch, SplitSwitchDecl

_TOKEN_TO_TILE = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
}


def load_stage(file_path):
    grid = []
    start_r, start_c = 0, 0
    switches = []
    bridge_groups = {}
    initial_open = set()
    split_switches = []

    with open(file_path, 'r') as f:
        lines = [line.rstrip('\n') for line in f]

    # Tách phần lưới (đến khi gặp dòng trống hoặc dòng lệnh) và phần khai báo
    grid_lines = []
    command_lines = []
    in_grid = True
    for line in lines:
        stripped = line.strip()
        if in_grid:
            if stripped == '' or stripped.split()[0] in ('BRIDGE', 'SWITCH', 'INIT', 'SPLIT'):
                in_grid = False
                if stripped:
                    command_lines.append(stripped)
            else:
                grid_lines.append(line)
        else:
            if stripped:
                command_lines.append(stripped)

    for r, line in enumerate(grid_lines):
        row_tokens = line.strip().split()
        row_data = []
        for c, token in enumerate(row_tokens):
            if token == 'S':
                start_r, start_c = r, c
                row_data.append(1)
            elif token in _TOKEN_TO_TILE:
                row_data.append(_TOKEN_TO_TILE[token])
            else:
                row_data.append(0)
        grid.append(row_data)

    for line in command_lines:
        parts = line.split()
        kind = parts[0]

        if kind == 'BRIDGE':
            group = parts[1]
            coords = list(map(int, parts[2:]))
            cells = tuple((coords[i], coords[i + 1]) for i in range(0, len(coords), 2))
            bridge_groups[group] = bridge_groups.get(group, ()) + cells

        elif kind == 'SWITCH':
            r, c = int(parts[1]), int(parts[2])
            sw_kind = parts[3]        # SOFT | HEAVY
            mode = parts[4]           # TOGGLE | PERMANENT
            group = parts[5]
            target_open = None
            if mode == 'PERMANENT':
                target_open = (parts[6] == 'OPEN')
            switches.append(Switch(r=r, c=c, kind=sw_kind, mode=mode,
                                    group=group, target_open=target_open))

        elif kind == 'INIT':
            group = parts[1]
            state = parts[2]
            if state == 'OPEN':
                initial_open.update(bridge_groups.get(group, ()))

        elif kind == 'SPLIT':
            r, c = int(parts[1]), int(parts[2])
            target_a = (int(parts[3]), int(parts[4]))
            target_b = (int(parts[5]), int(parts[6]))
            split_switches.append(SplitSwitchDecl(r=r, c=c, target_a=target_a, target_b=target_b))

    board = Board(
        grid=grid,
        switches=switches,
        bridge_groups=bridge_groups,
        initial_open_bridges=frozenset(initial_open),
        split_switches=split_switches,
    )
    return board, start_r, start_c


def to_switch_dicts(switches):
    """Tiện ích: chuyển List[Switch] -> List[dict] cho BloxorzCore (main.py dùng dict)."""
    return [
        {'r': sw.r, 'c': sw.c, 'kind': sw.kind, 'mode': sw.mode,
         'group': sw.group, 'target_open': sw.target_open}
        for sw in switches
    ]
