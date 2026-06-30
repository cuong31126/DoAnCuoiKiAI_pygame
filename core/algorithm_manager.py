from algorithms.adversarial import alpha_beta_search, expectimax_search, minimax_search
from algorithms.csp import backtracking_search, forward_checking_search, min_conflicts_search
from algorithms.informed import (
    
    astar_route,
    greedy_route,
    ida_star_route,
    
)
from algorithms.local_search import local_beam_search, simple_hill_climbing, simulated_annealing
from algorithms.uninformed import bfs_search, dfs_search, ucs_search
from algorithms.complex import and_or_search, partial_observation_search, no_observation_search
# import 6 file ở thư mục algorithms 


# trạm trung chuyển dữ liệu , nhận tên thuật toán từ UI sau đó gom 
class AlgorithmManager:
    """Dispatches the allowed algorithms for each level through one interface."""

    LEVEL_ALGORITHMS = {
        1: ["BFS", "DFS", "UCS"],
        2: ["A* Search", "IDA*", "Greedy Best-First"],
        3: ["Simple Hill Climbing", "Local Beam Search", "Simulated Annealing"],
        4: ["AND-OR Search", "Partial Observation", "No Observation"],
        5: ["Backtracking Search", "Forward Checking", "Min-Conflicts"],
        6: ["Minimax", "Alpha-Beta Pruning", "Expectimax"],
    }

# hàm khởi tạo , lưu lại đối tượng bản đồ 
    def __init__(self, hospital_map):
        self.hospital_map = hospital_map

# cập nhật lại bản đồ mới khi người chơi đổi màn 
    def set_map(self, hospital_map):
        self.hospital_map = hospital_map

# trả về ds tên thuật toán của level hiện tại để UI vẽ lên menu dropdown 
    def get_algorithms(self, level=None):
        return list(self.LEVEL_ALGORITHMS.get(level or self.hospital_map.level, []))

# hàm điều hướng 
    def run_algorithm(self, name, start=None, battery=None):
        hospital_map = self.hospital_map
        # lấy vị trí mặc định trên map 
        start = start or hospital_map.start
        # ko truyền lượng pin thì lấy giới hạn pin tới dda
        battery = hospital_map.battery_limit if battery is None else battery
        # lấy ds nhiệm vụ 
        tasks = hospital_map.remaining_tasks()
        if not tasks:
            return self._empty_success(name, start)

        if hospital_map.level == 1:
            goal = tasks[0].target
            if name == "BFS":
                return bfs_search(hospital_map, start, goal)
            if name == "DFS":
                return dfs_search(hospital_map, start, goal)
            return ucs_search(hospital_map, start, goal)

# tìm đường có heuristic qua chuỗi nhiều nhiệm vụ 
        if hospital_map.level == 2:
            if name == "A* Search":
                return astar_route(hospital_map, start, tasks)
            if name == "IDA*":
                return ida_star_route(hospital_map, start, tasks)
            if name == "Greedy Best-First":
                return greedy_route(hospital_map, start, tasks)
            return greedy_route(hospital_map, start, tasks)

# tối ưu thứ tự đi các nhiệm vụ 
        if hospital_map.level == 3:
            if name == "Simple Hill Climbing":
                return simple_hill_climbing(hospital_map, start, tasks)
            if name == "Local Beam Search":
                return local_beam_search(hospital_map, start, tasks)
            return simulated_annealing(hospital_map, start, tasks)

# môi trường bất địch 
        if hospital_map.level == 4:
            # gọi hàm bổ trợ để chọn ra 1 giường bệnh tối ưu làm đích goal 
            goal = self._best_task(start, tasks).target
            if name == "AND-OR Search":
                return and_or_search(hospital_map, start, goal)
            if name == "Partial Observation":
                return partial_observation_search(hospital_map, start, goal)
            return no_observation_search(hospital_map, start, goal)

# ràng buộc csp để xếp lịch làm việc 
        if hospital_map.level == 5:
            if name == "Backtracking Search":
                return backtracking_search(hospital_map, start, tasks)
            if name == "Forward Checking":
                return forward_checking_search(hospital_map, start, tasks)
            if name == "Min-Conflicts":
                return min_conflicts_search(hospital_map, start, tasks)
            return forward_checking_search(hospital_map, start, tasks)

# đối kháng  sẽ tính toán cả lượng pin hiện tại của robot 
        if name == "Minimax":
            return minimax_search(hospital_map, start, tasks, battery=battery)
        if name == "Alpha-Beta Pruning":
            return alpha_beta_search(hospital_map, start, tasks, battery=battery)
        return expectimax_search(hospital_map, start, tasks, battery=battery)

# chạy thử nghiệm tất cả thuật toán của level đố cùng lúc để lấy dữ liệu so sánh 
    def analyze_all(self, start=None, battery=None):
        return [self.run_algorithm(name, start=start, battery=battery) for name in self.get_algorithms()]



    def _best_task(self, start, tasks):
        def score(task):
            # tính khoảng cách mahattan từ robot đến giường bệnh 
            distance = abs(task.target[0] - start[0]) + abs(task.target[1] - start[1])
            deadline = task.deadline or 999 # ko có giới hạn time thì mặc đinh là 999 
            return (deadline, distance - task.priority * 2) # ưu tiên deadline nhỏ trc m 
# trả về giường bệnh có điểm thấp nhất 
        return min(tasks, key=score)


# hàm tạo kết quả mặc định khi ko còn nhiệm vụ nào để làm 
    def _empty_success(self, name, start):
        return {
            "name": name,
            "path": [start],
            "plan": [],
            "cost": 0,
            "path_length": 0,
            "nodes_expanded": 0,
            "runtime_ms": 0.0,
            "success": True,
            "message": "All tasks already complete.",
        }


# hàm bổ trợ này đóng vai trò như một bộ lọc quyết định nhanh.
# Nó tính toán dựa trên 3 yếu tố: bệnh nhân nào sắp hết thời gian cứu 
# (deadline), bệnh nhân nào ở gần robot nhất (distance), 
# và bệnh nhân nào có độ nguy kịch cao nhất (priority). 
# Người nào có số điểm tối ưu nhất sẽ được chọn làm đích đến (goal) duy nhất cho robot ở lượt chạy đó.
