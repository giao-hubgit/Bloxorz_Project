import heapq
import time
import tracemalloc
import math

class AStarSolver:
    def __init__(self, grid, start_r, start_c):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.start_state = (start_r, start_c, 'STANDING')
        self.goal_r, self.goal_c = self.find_goal()

    def find_goal(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 2:
                    return r, c
        return -1, -1

    def heuristic(self, r, c, orientation):
        """
        Hàm ước lượng khoảng cách (Heuristic) sử dụng Manhattan Distance.
        """
        # Tính khoảng cách Manhattan từ toạ độ chính của khối đến đích
        manhattan_dist = abs(r - self.goal_r) + abs(c - self.goal_c)
        
        # Vì mỗi bước lăn khối có thể di chuyển tối đa 2 ô, ta chia 2 để đảm bảo Admissible
        h = manhattan_dist / 2.0
        
        # Nếu không ở tư thế đứng, chắc chắn cần tốn thêm ít nhất một thao tác để đứng lên
        # (Chỉ cộng thêm một trọng số rất nhỏ để không vi phạm tính Admissible)
        if orientation != 'STANDING':
            h += 0.5 
            
        return h

    def get_successors(self, r, c, orientation):
        """
        Mô phỏng lại logic di chuyển từ bloxorz_core.py để sinh các trạng thái con.
        """
        successors = []
        moves = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        for move in moves:
            new_r, new_c, new_ori = r, c, orientation
            
            if orientation == 'STANDING':
                if move == 'LEFT': new_ori, new_r, new_c = 'LYING_H', r, c - 2
                elif move == 'RIGHT': new_ori, new_r, new_c = 'LYING_H', r, c + 1
                elif move == 'UP': new_ori, new_r, new_c = 'LYING_V', r - 2, c
                elif move == 'DOWN': new_ori, new_r, new_c = 'LYING_V', r + 1, c
            elif orientation == 'LYING_H':
                if move == 'LEFT': new_ori, new_r, new_c = 'STANDING', r, c - 1
                elif move == 'RIGHT': new_ori, new_r, new_c = 'STANDING', r, c + 2
                elif move == 'UP': new_ori, new_r, new_c = 'LYING_H', r - 1, c
                elif move == 'DOWN': new_ori, new_r, new_c = 'LYING_H', r + 1, c
            elif orientation == 'LYING_V':
                if move == 'LEFT': new_ori, new_r, new_c = 'LYING_V', r, c - 1
                elif move == 'RIGHT': new_ori, new_r, new_c = 'LYING_V', r, c + 1
                elif move == 'UP': new_ori, new_r, new_c = 'STANDING', r - 1, c
                elif move == 'DOWN': new_ori, new_r, new_c = 'STANDING', r + 2, c
                
            if self.is_valid(new_r, new_c, new_ori):
                successors.append((new_r, new_c, new_ori, move))
                
        return successors

    def is_valid(self, r, c, orientation):
        """
        Kiểm tra trạng thái hợp lệ (không rơi ra ngoài bàn cờ hoặc rơi xuống lỗ trống).
        """
        cells = []
        if orientation == 'STANDING': cells = [(r, c)]
        elif orientation == 'LYING_H': cells = [(r, c), (r, c + 1)]
        elif orientation == 'LYING_V': cells = [(r, c), (r + 1, c)]
        
        for pr, pc in cells:
            if pr < 0 or pr >= self.rows or pc < 0 or pc >= self.cols:
                return False
            if self.grid[pr][pc] == 0:
                return False
        return True

    def solve(self):
        # Bắt đầu theo dõi bộ nhớ và thời gian (Yêu cầu đo 4 thông số thực nghiệm)
        tracemalloc.start()
        start_time = time.time()
        
        # Priority Queue lưu trữ: (f_score, tie_breaker, g_score, state, path)
        pq = []
        counter = 0  # Dùng để phá vỡ thế hòa (tie-breaker) khi f_score bằng nhau
        
        start_h = self.heuristic(self.start_state[0], self.start_state[1], self.start_state[2])
        heapq.heappush(pq, (start_h, counter, 0, self.start_state, []))
        
        visited = set()
        expanded_nodes = 0
        
        while pq:
            f, _, g, current_state, path = heapq.heappop(pq)
            
            if current_state in visited:
                continue
            visited.add(current_state)
            expanded_nodes += 1
            
            r, c, orientation = current_state
            
            # Kiểm tra điều kiện thắng
            if orientation == 'STANDING' and self.grid[r][c] == 2:
                end_time = time.time()
                current_memory, peak_memory = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                search_time = end_time - start_time
                peak_memory_kb = peak_memory / 1024
                path_length = len(path)
                
                return {
                    "path": path,
                    "time_sec": search_time,
                    "peak_memory_kb": peak_memory_kb,
                    "expanded_nodes": expanded_nodes,
                    "path_length": path_length
                }
            
            # Sinh các trạng thái con
            for next_r, next_c, next_ori, move in self.get_successors(r, c, orientation):
                next_state = (next_r, next_c, next_ori)
                if next_state not in visited:
                    new_g = g + 1  # Giả định chi phí cơ bản (cost function) là 1 cho mỗi bước di chuyển
                    new_h = self.heuristic(next_r, next_c, next_ori)
                    new_f = new_g + new_h
                    
                    counter += 1
                    heapq.heappush(pq, (new_f, counter, new_g, next_state, path + [move]))
                    
        # Không tìm thấy đường đi
        tracemalloc.stop()
        return None