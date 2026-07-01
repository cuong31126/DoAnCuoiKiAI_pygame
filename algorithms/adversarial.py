import time

from algorithms.informed import astar_path

# ds 5 quyết định của robot : đi đến nhiệm vụ , đi sạc , chờ , lập kế hoạch lại , ưu tiên nhiệm vụ khẩn cấp
ACTION_NAMES = ["go_to_task", "go_to_charge", "wait", "replan", "prioritize_emergency"]
# ds 3 trạng thái môi trường : rõ ràng , đông đúc , bị chặn kèm xác suất xảy ra tương ứng 
ENV_STATES = [
    ("clear", 0.55),
    ("crowded", 0.30),
    ("blocked", 0.15),
]

# hàm chọn nv tối ưu nhất 
def _best_task(start, tasks, emergency_only=False):
    # ưu tiên nếu là urgent , nếu ko có thì chọn tất cả các nhiệm vụ
    filtered = [task for task in tasks if task.urgent] if emergency_only else tasks
    if not filtered:
        filtered = tasks
    # chọn nhiệm vụ có deadline gấp nhất , nếu ko có deadline thì chọn nhiệm vụ gần nhất và ưu tiên reward cao hơn
    return min(
        filtered,
        key=lambda task: (
            task.deadline or 999,
            abs(task.target[0] - start[0]) + abs(task.target[1] - start[1]) - task.priority * 2,
        ),
    )

# tìm trạm sạc gần nhất và đường đi đến đó , tránh các ô nguy hiểm nếu có
def _nearest_charge(hospital_map, start, avoid=None):
    if not hospital_map.charge_stations:
        return None, None
    best_station = None
    best_result = None
    # gọi A* tìm đường đi và trả về trạm sạc có chi phí đường đi cost min 
    for station in hospital_map.charge_stations:
        result = astar_path(hospital_map, start, station, avoid=avoid)
        if result["success"] and (best_result is None or result["cost"] < best_result["cost"]):
            best_station = station
            best_result = result
    return best_station, best_result

# hàm tính toán lộ trình hành động 
def _action_path(hospital_map, start, tasks, action, avoid_dynamic=False):
    avoid = hospital_map.predicted_dynamic_positions(steps=4) if avoid_dynamic else None
    if action == "go_to_charge":
        _station, result = _nearest_charge(hospital_map, start, avoid=avoid)
        return result
    if action == "wait":
        return {"path": [start], "cost": 0, "nodes": 1, "success": True}
    task = _best_task(start, tasks, emergency_only=action == "prioritize_emergency")
    return astar_path(hospital_map, start, task.target, avoid=avoid)


# tính hàm mực tiêu độ hữu dựng , tính điểm chất lượng 
def _utility(hospital_map, start, tasks, action, env_state, battery=None):
    avoid_dynamic = bool(hospital_map.dynamic_obstacles) and action != "wait"
    result = _action_path(hospital_map, start, tasks, action, avoid_dynamic=avoid_dynamic)
    if not result or not result["success"]:
        return -999, result
    # kiểm tra pin . nếu đi lố hết pin phạt nặng -999 - lượng pin thiếu hụt * 25
    distance = result["cost"]
    battery_budget = hospital_map.battery_limit if battery is None else battery
    if action != "go_to_charge" and distance > battery_budget:
        return -999 - (distance - battery_budget) * 25, result
    if action == "go_to_charge" and distance > battery_budget:
        return -999 - (distance - battery_budget) * 25, result
#tính tonas phan thuong va hinh phat 
    target_task = _best_task(start, tasks, emergency_only=action == "prioritize_emergency")
    reward = 0 if action in ("wait", "go_to_charge") else target_task.reward + target_task.priority * 15
    emergency_bonus = 50 if action == "prioritize_emergency" and target_task.urgent else 0
    distance_penalty = distance * 4
    battery_penalty = max(0, distance - battery_budget) * 10
    late_penalty = 60 if target_task.deadline and distance > target_task.deadline else 0
    collision_penalty = {"clear": 0, "crowded": 25, "blocked": 70}[env_state]
    charge_bonus = max(0, 45 - battery_budget) if action == "go_to_charge" else 0
    wait_penalty = 30 if action == "wait" else 0
    utility = reward + emergency_bonus + charge_bonus - distance_penalty - battery_penalty - collision_penalty - late_penalty - wait_penalty
    return utility, result

# đóng gói kq đầu ra cho hud
def _finish(name, started, action, utility, nodes, path_result, message):
    path = path_result["path"] if path_result else []
    return {
        "name": name,
        "path": path,
        "plan": [action],
        "cost": path_result["cost"] if path_result else 0,
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": nodes + (path_result["nodes"] if path_result else 0),
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": bool(path),
        "message": message,
        "visited": path_result.get("visited", path) if path_result else [],
        "selected_action": action,
        "utility": round(utility, 2),
    }

# môi trường nguy hiểm , luôn cho kịch bản tồi tệ nhaats
def minimax_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    best = None
    nodes = 0
    for action in ACTION_NAMES: # lặp max quyết định của robot 
        worst_utility = None
        worst_result = None
        for env_state, _prob in ENV_STATES: # vòng lặp min ( môi trường)
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            if worst_utility is None or utility < worst_utility:
                worst_utility = utility # tìm kịch bản tệ nhất cho hd này
                worst_result = result
        if best is None or worst_utility > best[1]:
            best = (action, worst_utility, worst_result) # robot chon hd có kq tệ nhất là tốt nhất 
    return _finish("Minimax", started, best[0], best[1], nodes, best[2], "Environment chooses the worst outcome.")

# cắt tỉa , giống minimaxnhungw cắt tỉa nhánh 
def alpha_beta_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    alpha = -10_000 # giá trị tối thiểu nút max
    best = None
    nodes = 0
    for action in ACTION_NAMES: 
        beta = 10_000 # giá trị tối đa nút min 
        value = 10_000
        chosen_result = None
        for env_state, _prob in ENV_STATES:
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            if utility < value:
                value = utility
                chosen_result = result
            beta = min(beta, value)
            if beta <= alpha:
                break # phát hiện tỉa liền 
        if best is None or value > best[1]:
            best = (action, value, chosen_result)
        alpha = max(alpha, value)
    return _finish("Alpha-Beta Pruning", started, best[0], best[1], nodes, best[2], "Same game model as minimax with pruning.")

# xảy ra ngẫu nhiên theo xác suất robot sẽ tối ưu hóa giá trị kỳ vọng 
def expectimax_search(hospital_map, start, tasks, battery=None):
    started = time.perf_counter()
    best = None
    nodes = 0
    for action in ACTION_NAMES: # max
        expected = 0.0
        representative = None
        for env_state, probability in ENV_STATES: # chance cơ hội xác xuát 
            nodes += 1
            utility, result = _utility(hospital_map, start, tasks, action, env_state, battery=battery)
            expected += utility * probability # tính giá trị kỳ vọng 
            if env_state == "clear":
                representative = result
        if best is None or expected > best[1]:
            best = (action, expected, representative) # chọn hd có giá trị kỳ vọng lớn nhất 
    return _finish("Expectimax", started, best[0], best[1], nodes, best[2], "Environment is modeled as probabilistic.")


# Trong code, biến best là một Tuple (bộ dữ liệu) gồm 3 phần tử, 
# lưu trữ thông tin về quyết định tối ưu nhất mà Robot 
# chọn được sau khi tính toán:

# python


# best = (action, expected, representative)
# Cụ thể, cấu trúc của best gồm:

# best[0] (Hành động - action): Lưu tên hành động được chọn (Kiểu chuỗi - String, ví dụ: "go_to_task" hoặc "go_to_charge").
# best[1] (Độ hữu dụng kỳ vọng - expected): Lưu điểm số kỳ vọng trung bình cao nhất tính được cho hành động đó (Kiểu số thực - Float, ví dụ: 150.5).
# best[2] (Lộ trình đại diện - representative): Lưu dict kết quả tìm đường A* của hành động đó trong kịch bản thời tiết thông thoáng "clear" (để Robot lấy lộ trình này di chuyển thực tế trên bản đồ).