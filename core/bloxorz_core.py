
from core.state import VOID, FLOOR, GOAL, FRAGILE, BRIDGE, SOFT_SWITCH, HEAVY_SWITCH, SPLIT_SWITCH

class BloxorzCore:
    def __init__(self, grid, start_r, start_c, switches=None, bridge_groups=None,
                 initial_open_bridges=None, split_switches=None):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.r = start_r
        self.c = start_c
        self.orientation = 'STANDING'
        self.fall_void_cell = None

        self.switches = switches or []
        self.bridge_groups = bridge_groups or {}
        self.open_bridges = set(initial_open_bridges or set())

        self.last_triggered_switches = []

        self.split_switches = split_switches or []
        self.split_mode = False
        self.cubes = []
        self.active_cube_index = 0
        self.just_merged = False

    def get_occupied_cells(self):
        if self.orientation == 'STANDING':
            return [(self.r, self.c)]
        elif self.orientation == 'LYING_H':
            return [(self.r, self.c), (self.r, self.c + 1)]
        elif self.orientation == 'LYING_V':
            return [(self.r, self.c), (self.r + 1, self.c)]

    def tile_at(self, r, c):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return VOID
        return self.grid[r][c]

    def _is_passable(self, r, c):
        tile = self.tile_at(r, c)
        if tile == VOID:
            return False
        if tile == BRIDGE:
            return (r, c) in self.open_bridges
        return True

    def _apply_switches(self, cells):
        triggered = []
        cell_set = set(cells)
        for sw in self.switches:
            pos = (sw['r'], sw['c'])
            if pos not in cell_set:
                continue

            if sw['kind'] == 'SOFT':
                is_triggered = True
            elif sw['kind'] == 'HEAVY':
                is_triggered = (self.orientation == 'STANDING' and len(cells) == 1 and cells[0] == pos)
            else:
                is_triggered = False

            if not is_triggered:
                continue

            triggered.append(sw)
            group_cells = self.bridge_groups.get(sw['group'], ())
            if sw['mode'] == 'TOGGLE':
                for cell in group_cells:
                    if cell in self.open_bridges:
                        self.open_bridges.discard(cell)
                    else:
                        self.open_bridges.add(cell)
            elif sw['mode'] == 'PERMANENT':
                for cell in group_cells:
                    if sw.get('target_open'):
                        self.open_bridges.add(cell)
                    else:
                        self.open_bridges.discard(cell)

        self.last_triggered_switches = triggered

    def move(self, direction):
        if self.split_mode:
            return self._move_active_cube(direction)
        return self._move_block(direction)

    def switch_active_cube(self):
        if self.split_mode and len(self.cubes) == 2:
            self.active_cube_index = 1 - self.active_cube_index

    def _move_active_cube(self, direction):
        dr, dc = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}[direction]
        cube = self.cubes[self.active_cube_index]
        new_r, new_c = cube['r'] + dr, cube['c'] + dc

        if not self._is_passable(new_r, new_c):
            cube['r'], cube['c'] = new_r, new_c
            return "LOSE_FALL"

        cube['r'], cube['c'] = new_r, new_c

        for sw in self.switches:
            if sw['kind'] != 'SOFT':
                continue
            if (sw['r'], sw['c']) != (new_r, new_c):
                continue
            group_cells = self.bridge_groups.get(sw['group'], ())
            if sw['mode'] == 'TOGGLE':
                for cell in group_cells:
                    if cell in self.open_bridges:
                        self.open_bridges.discard(cell)
                    else:
                        self.open_bridges.add(cell)
            elif sw['mode'] == 'PERMANENT':
                for cell in group_cells:
                    if sw.get('target_open'):
                        self.open_bridges.add(cell)
                    else:
                        self.open_bridges.discard(cell)

        merged = self._try_merge()
        if merged:
            return self.check_status()

        return "CONTINUE"

    def _try_merge(self):
        a, b = self.cubes[0], self.cubes[1]
        if a['r'] == b['r'] and abs(a['c'] - b['c']) == 1:
            left = a if a['c'] < b['c'] else b
            self.orientation = 'LYING_H'
            self.r, self.c = left['r'], left['c']
        elif a['c'] == b['c'] and abs(a['r'] - b['r']) == 1:
            top = a if a['r'] < b['r'] else b
            self.orientation = 'LYING_V'
            self.r, self.c = top['r'], top['c']
        else:
            return False

        self.split_mode = False
        self.cubes = []
        self.active_cube_index = 0
        self.just_merged = True
        return True

    def _check_split_trigger(self):
        if self.orientation != 'STANDING':
            return False
        for sw in self.split_switches:
            if (sw['r'], sw['c']) != (self.r, self.c):
                continue
            ta, tb = sw['target_a'], sw['target_b']
            self.split_mode = True
            self.cubes = [{'r': ta[0], 'c': ta[1]}, {'r': tb[0], 'c': tb[1]}]
            self.active_cube_index = 0
            return True
        return False

    def _move_block(self, direction):
        r, c = self.r, self.c
        ori = self.orientation
        if ori == 'STANDING':
            if direction == 'LEFT':
                self.orientation, self.r, self.c = 'LYING_H', r, c - 2
            elif direction == 'RIGHT':
                self.orientation, self.r, self.c = 'LYING_H', r, c + 1
            elif direction == 'UP':
                self.orientation, self.r, self.c = 'LYING_V', r - 2, c
            elif direction == 'DOWN':
                self.orientation, self.r, self.c = 'LYING_V', r + 1, c
        elif ori == 'LYING_H':
            if direction == 'LEFT':
                self.orientation, self.r, self.c = 'STANDING', r, c - 1
            elif direction == 'RIGHT':
                self.orientation, self.r, self.c = 'STANDING', r, c + 2
            elif direction == 'UP':
                self.orientation, self.r, self.c = 'LYING_H', r - 1, c
            elif direction == 'DOWN':
                self.orientation, self.r, self.c = 'LYING_H', r + 1, c
        elif ori == 'LYING_V':
            if direction == 'LEFT':
                self.orientation, self.r, self.c = 'LYING_V', r, c - 1
            elif direction == 'RIGHT':
                self.orientation, self.r, self.c = 'LYING_V', r, c + 1
            elif direction == 'UP':
                self.orientation, self.r, self.c = 'STANDING', r - 1, c
            elif direction == 'DOWN':
                self.orientation, self.r, self.c = 'STANDING', r + 2, c

        self._apply_switches(self.get_occupied_cells())

        if self._check_split_trigger():
            return "CONTINUE"

        return self.check_status()

    def check_status(self):
        cells = self.get_occupied_cells()
        void_cells = []

        for (pr, pc) in cells:
            if not self._is_passable(pr, pc):
                void_cells.append((pr, pc))

        if void_cells:
            if len(cells) == 2 and len(void_cells) == 1:
                self.fall_void_cell = void_cells[0]
            else:
                self.fall_void_cell = None
            return "LOSE_FALL"

        if self.orientation == 'STANDING' and self.tile_at(self.r, self.c) == FRAGILE:
            self.fall_void_cell = None
            return "LOSE_FALL"

        self.fall_void_cell = None
        if self.orientation == 'STANDING' and self.tile_at(self.r, self.c) == GOAL:
            return "WIN"
        return "CONTINUE"
