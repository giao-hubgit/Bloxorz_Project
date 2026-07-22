
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
            sw_kind = parts[3]
            mode = parts[4]
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
    return [
        {'r': sw.r, 'c': sw.c, 'kind': sw.kind, 'mode': sw.mode,
         'group': sw.group, 'target_open': sw.target_open}
        for sw in switches
    ]

def split_dicts(split_switches):
    return [
        {'r': s.r, 'c': s.c, 'target_a': s.target_a, 'target_b': s.target_b}
        for s in split_switches
    ]
