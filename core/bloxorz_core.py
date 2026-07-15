class BloxorzCore:
    def __init__(self, grid, start_r, start_c):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.r = start_r
        self.c = start_c
        self.orientation = 'STANDING' 
        self.fall_void_cell = None

    def get_occupied_cells(self):
        if self.orientation == 'STANDING': return [(self.r, self.c)]
        elif self.orientation == 'LYING_H': return [(self.r, self.c), (self.r, self.c + 1)]
        elif self.orientation == 'LYING_V': return [(self.r, self.c), (self.r + 1, self.c)]

    def move(self, direction):
        r, c = self.r, self.c
        ori = self.orientation
        if ori == 'STANDING':
            if direction == 'LEFT': self.orientation, self.r, self.c = 'LYING_H', r, c - 2
            elif direction == 'RIGHT': self.orientation, self.r, self.c = 'LYING_H', r, c + 1
            elif direction == 'UP': self.orientation, self.r, self.c = 'LYING_V', r - 2, c
            elif direction == 'DOWN': self.orientation, self.r, self.c = 'LYING_V', r + 1, c
        elif ori == 'LYING_H':
            if direction == 'LEFT': self.orientation, self.r, self.c = 'STANDING', r, c - 1
            elif direction == 'RIGHT': self.orientation, self.r, self.c = 'STANDING', r, c + 2
            elif direction == 'UP': self.orientation, self.r, self.c = 'LYING_H', r - 1, c
            elif direction == 'DOWN': self.orientation, self.r, self.c = 'LYING_H', r + 1, c
        elif ori == 'LYING_V':
            if direction == 'LEFT': self.orientation, self.r, self.c = 'LYING_V', r, c - 1
            elif direction == 'RIGHT': self.orientation, self.r, self.c = 'LYING_V', r, c + 1
            elif direction == 'UP': self.orientation, self.r, self.c = 'STANDING', r - 1, c
            elif direction == 'DOWN': self.orientation, self.r, self.c = 'STANDING', r + 2, c
        return self.check_status()

    def check_status(self):
        cells = self.get_occupied_cells()
        void_cells = []
        
        # Tìm các ô mà block chạm vào là void
        for pr, pc in cells:
            is_void = False
            if pr < 0 or pr >= self.rows or pc < 0 or pc >= self.cols:
                is_void = True
            elif self.grid[pr][pc] == 0:
                is_void = True
                
            if is_void:
                void_cells.append((pr, pc))
        
        if void_cells:
            if len(cells) == 2 and len(void_cells) == 1:
                self.fall_void_cell = void_cells[0]
            else:
                self.fall_void_cell = None
            return "LOSE_FALL"
            
        self.fall_void_cell = None
        if self.orientation == 'STANDING' and self.grid[self.r][self.c] == 2: 
            return "WIN"
        return "CONTINUE"