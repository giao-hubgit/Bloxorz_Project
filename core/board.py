def load_stage(file_path):
    grid = []
    start_r, start_c = 0, 0
    with open(file_path, 'r') as file:
        for r, line in enumerate(file.readlines()):
            row_tokens = line.strip().split()
            row_data = []
            for c, token in enumerate(row_tokens):
                if token == 'S':
                    start_r, start_c = r, c
                    row_data.append(1)
                elif token == '2': row_data.append(2)
                elif token == '1': row_data.append(1)
                else: row_data.append(0)
            grid.append(row_data)
    return grid, start_r, start_c