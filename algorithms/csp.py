from itertools import permutations
import random
import time

from algorithms.informed import astar_path


# cài đặt hạt giống nhẫu nhiên cố định là 7 cho min conflict
RNG = random.Random(7)

# ghep 2 ds tọa độ và loại ổ ptu trùng ở điẻm tiếp nối 
def _merge(first, second):
    if not first:
        return list(second)
    if not second:
        return list(first)
    return list(first) + list(second)[1:]

# hàm đánh giá và tính lỗi ràng buộc 
def _evaluate_order(hospital_map, start, tasks, order):
    # khởi tạo biến để theo doi trang thai robot quang duong pin diem số 
    current = start
    route = []
    total_cost = 0
    elapsed = 0
    battery = hospital_map.battery_limit
    violations = 0
    nodes = 0
    visited = []
    score = 0
    plan = []
    dangerous = hospital_map.predicted_dynamic_positions(steps=4) # dự đoán trc hd trong 4 buoc tiep tho de đưa vào tạp ô cám 

# duyệt qua từng task theo thứ tự order 
    for index in order:
        task = tasks[index]
        # dùng A* tìm đường từ vị trí hiện tại đến vị trí mục tiêu của task, tránh các ô nguy hiểm
        result = astar_path(hospital_map, current, task.target, avoid=dangerous)
        nodes += result["nodes"]
        visited.extend(result["visited"])
        # ràng buộc 1 : ko có đường đi vio + 4 
        if not result["success"]:
            violations += 4
            continue
        # cập nhật lộ trình tọa độ , tổng chí phí , tg trôi qua , và trừ năng lượng pin 
        route = _merge(route, result["path"])
        total_cost += result["cost"]
        elapsed += result["cost"]
        battery -= result["cost"]
        #  rằng buộc 2 : tại ddaay robot bị âm thì phạt 2 
        if battery < 0:
            violations += 2
        # ràng buộc 3 : nếu có deadline và tg trôi qua > deadline thì phạt 3 nếu task khẩn cấp , 1 nếu ko khẩn cấp
        if task.deadline and elapsed > task.deadline:
            violations += 3 if task.urgent else 1
        # ràng buộc 4 : nếu vị trí mục tiêu của task nằm trong các ô nguy hiểm thì phạt 1
        if task.target in dangerous:
            violations += 1
        # cập nhật điểm thương ưu tiên ô có task priority cao 
        score += task.reward + task.priority * 12
        current = task.target
        plan.append(task.task_id)

    # ràn buộc 5 : sai thứ tự ưu tiên +1 lôi
    for left, right in zip(order, order[1:]):
        if tasks[left].priority < tasks[right].priority and tasks[right].urgent:
            violations += 1

    # lấy điểm thường trừ đi điểm phạt 
    score -= violations * 40 + total_cost
    # trả về kq ddansh giá 
    return {
        "order": list(order),
        "path": route,
        "plan": plan,
        "cost": total_cost,
        "nodes": nodes,
        "visited": visited,  # số lỗi vi phạm ràng buộc 
        "violations": violations,
        "score": score,
        "success": bool(route) and violations == 0,
    }


#  đóng gói thông số chạy thuật toán cho hub hiển thị 
def _finish(name, started, evaluation, expanded, message):
    return {
        "name": name,
        "path": evaluation["path"],
        "plan": evaluation["plan"],
        "cost": evaluation["cost"],
        "path_length": max(0, len(evaluation["path"]) - 1),
        "nodes_expanded": evaluation["nodes"] + expanded,
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": bool(evaluation["path"]),
        "message": message,
        "visited": evaluation.get("visited", evaluation["path"]),
        "constraint_violations": evaluation["violations"],
        "score": evaluation["score"],
    }

# lọc ra phương án tốt nhất trong các ứng viên 
def _best_by_constraints(candidates):
    return min(candidates, key=lambda item: (item["violations"], -item["score"], item["cost"]))

# start S(1,1) , pin tối đa = 75 , thời hạn màn chơi 110 , có 4 nv [E1, T1 ,T2, T3]
# tìm kiếm quay lui (backtracking) để tìm ra thứ tự thực hiện các task tối ưu nhất dựa trên các ràng buộc về deadline, pin, và vị trí nguy hiểm.
def backtracking_search(hospital_map, start, tasks):
    started = time.perf_counter()
    order_domain = range(len(tasks))
    best = None
    expanded = 0
    # khởi tạo miền giá trị và biến đếm số bước đệ quy 
    def backtrack(prefix, remaining):
        nonlocal best, expanded
        # tăng biến điếm bước duyệt mỗi khi gọi hàm 
        expanded += 1
        # đk dừng đệ quy 
        if not remaining:
            evaluation = _evaluate_order(hospital_map, start, tasks, prefix)
            if best is None or (evaluation["violations"], -evaluation["score"]) < (best["violations"], -best["score"]):
                best = evaluation
            return
    # sx theo deadline và priority để ưu tiên các task quan trọng hơn
    # với priority cao cho - sau đo sort để đưa priority leen đầu nếu deadline = nhau 
        for index in sorted(remaining, key=lambda i: (tasks[i].deadline or 999, -tasks[i].priority)):
            backtrack(prefix + [index], [item for item in remaining if item != index])

    backtrack([], list(order_domain))
    message = "Perfect CSP plan found." if best and best["violations"] == 0 else "No perfect plan; selected lowest-conflict order."
    return _finish("Backtracking Search", started, best, expanded, message)


# thuật toán quay lui có kiểm tra ràng buộc trước (forward checking) để loại bỏ các nhánh không khả thi sớm hơn, giúp giảm số lượng trạng thái cần duyệt.
def forward_checking_search(hospital_map, start, tasks):
    started = time.perf_counter()
    order_domain = range(len(tasks))
    best = None
    expanded = 0
    dangerous = hospital_map.predicted_dynamic_positions(steps=4)
    # mô phỏng thử chuỗi nhiệm vụ đã gán 1 phân 
    # nếu robot bị hết pin , trễ deadline or bị kẹt đường trả vè none
    def partial_state(prefix):
        current = start
        elapsed = 0
        battery = hospital_map.battery_limit
        for index in prefix:
            task = tasks[index]
            result = astar_path(hospital_map, current, task.target, avoid=dangerous)
            if not result["success"]:
                return None
            elapsed += result["cost"]
            battery -= result["cost"]
            if battery < 0:
                return None
            if task.deadline and elapsed > task.deadline:
                return None
            current = task.target
        return current, elapsed, battery
    # lấy trạng thái hiện tại vt , thoi gian , pin sau ki da thuc hien xong pphanlo trinh prefix 
    def forward_ok(prefix, remaining):
        state = partial_state(prefix)
        if state is None:
            return False
        current, elapsed, battery = state
        # các nhiệm vụ chưa xếp 
        for index in remaining:
            task = tasks[index]
            
            result = astar_path(hospital_map, current, task.target, avoid=dangerous)
            # kt đường đi có khả thi ko , nếu ko => false
            if not result["success"]:
                return False
            # tính toán thời gian dự kiến và pin sau khi thực hiện nhiệm vụ này
            projected_elapsed = elapsed + result["cost"]
            # tính toán pin dự kiến sau khi thực hiện nhiệm vụ này
            if result["cost"] > battery:
                return False
            # nếu có deadline và tg dự kiến > deadline => false
            if task.deadline and projected_elapsed > task.deadline:
                return False
        return True

    def backtrack(prefix, remaining):
        nonlocal best, expanded
        expanded += 1
        # cắt tỉa sớm 
        if not forward_ok(prefix, remaining):
            return
        if not remaining:
            evaluation = _evaluate_order(hospital_map, start, tasks, prefix)
            if best is None or (evaluation["violations"], -evaluation["score"], evaluation["cost"]) < (
                best["violations"],
                -best["score"],
                best["cost"],
            ):
                best = evaluation
            return
        for index in sorted(remaining, key=lambda i: (tasks[i].deadline or 999, -tasks[i].priority)):
            backtrack(prefix + [index], [item for item in remaining if item != index])

    backtrack([], list(order_domain))
    if best is None:
        best = _best_by_constraints([_evaluate_order(hospital_map, start, tasks, order) for order in permutations(order_domain)])
    message = "Forward checking pruned infeasible deadline or battery branches early."
    return _finish("Forward Checking", started, best, expanded, message)

# thuật toán giảm thiểu xug đột 
def min_conflicts_search(hospital_map, start, tasks):
    started = time.perf_counter()
    order = list(range(len(tasks)))
    RNG.shuffle(order) # khởi tạo 1 chuỗi nv ngẫu nhiên tráo bài 
    best = _evaluate_order(hospital_map, start, tasks, order)
    expanded = 0
    # vòng lặp 160 lần sửa lỗi . nếu i phạm ràng buộc = 0 ,lộ trình hoàn hảo 
    for _ in range(160):
        expanded += 1
        if best["violations"] == 0:
            break
        # nếu chuỗi còn lỗi vi phạm thì 
        # chọn ngẫu nhiên 2 nv bất kỳ và hoán đổi ị trí của chúng cho nhau 
        a, b = RNG.sample(range(len(order)), 2)
        candidate_order = list(order)
        candidate_order[a], candidate_order[b] = candidate_order[b], candidate_order[a]
        # nếu phép hoán đổi giảm số lỗi i phạm => cập nhật phương án mới này 
        candidate = _evaluate_order(hospital_map, start, tasks, candidate_order)
        if (candidate["violations"], -candidate["score"]) <= (best["violations"], -best["score"]):
            order = candidate_order
            best = candidate

    message = "Min-conflicts reduced violations by local swaps."
    return _finish("Min-Conflicts", started, best, expanded, message)



