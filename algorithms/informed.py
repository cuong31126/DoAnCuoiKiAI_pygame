import heapq
import time


def manhattan(a, b):
    """
    Tính khoảng cách Manhattan giữa hai điểm a và b trên lưới tọa độ.
    Công thức: |x1 - x2| + |y1 - y2|
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(parent, start, goal):
    """
    Tái dựng lại đường đi từ điểm xuất phát (start) đến điểm đích (goal)
    bằng cách truy vết ngược từ goal về start thông qua từ điển parent.
    """
    # Nếu đích không nằm trong danh sách parent và đích khác điểm xuất phát -> Không tìm thấy đường
    if goal not in parent and goal != start:
        return []
    
    node = goal
    path = [node]
    # Duyệt ngược từ đích về nguồn
    while node != start:
        node = parent[node]
        path.append(node)
    
    # Đảo ngược danh sách để có đường đi từ start đến goal
    path.reverse()
    return path


def _runtime_result(name, started, path, plan, cost, nodes, success, message, visited=None, extra=None):
    """
    Hàm phụ trợ định dạng kết quả trả về của thuật toán, bao gồm thời gian chạy (runtime_ms),
    độ dài đường đi, số node đã duyệt và trạng thái thành công.
    """
    result = {
        "name": name,
        "path": path,
        "plan": plan,
        "cost": cost,
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": nodes,
        "runtime_ms": (time.perf_counter() - started) * 1000, # Tính thời gian trôi qua theo mili giây
        "success": success,
        "message": message,
        "visited": visited or [],
    }
    # Cập nhật thêm các thông tin phụ trợ nếu có (ví dụ: số vòng lặp của IDA*)
    if extra:
        result.update(extra)
    return result


def _search(hospital_map, start, goal, name, weight=1.0, greedy=False, avoid=None):
    """
    Hàm cốt lõi thực hiện thuật toán tìm kiếm đường đi có thông tin trên bản đồ.
    Có thể cấu hình thành A* Search (g + h) hoặc Greedy Best-First Search (chỉ dùng h).
    
    Tham số:
    - hospital_map: Bản đồ lưới bệnh viện
    - start: Điểm xuất phát (x, y)
    - goal: Điểm đích (x, y)
    - name: Tên thuật toán hiển thị
    - weight: Trọng số của heuristic
    - greedy: True nếu chạy Greedy Best-First, False nếu chạy A*
    - avoid: Tập hợp các ô cần tránh (ví dụ: ô có vật cản động ở Level 4)
    """
    avoid = set(avoid or [])
    # Khởi tạo Priority Queue (Heap): lưu trữ tuple (độ ưu tiên, chi phí thực tế g, node hiện tại)
    heap = [(0, 0, start)]
    # Lưu vết cha của mỗi node để tái dựng đường đi
    parent = {start: start}
    # Lưu chi phí thực tế nhỏ nhất từ start đến mỗi node
    g_score = {start: 0}
    # Danh sách thứ tự các node đã được duyệt qua (phục vụ trực quan hóa)
    visited = []
    # Tập hợp các node đã lấy ra khỏi heap và duyệt xong (closed set)
    closed = set()

    while heap:
        # Lấy node có độ ưu tiên thấp nhất (tốt nhất) ra khỏi Priority Queue
        _, cost, node = heapq.heappop(heap)
        
        # Nếu node này đã được duyệt và đóng, bỏ qua để tránh trùng lặp
        if node in closed:
            continue
        closed.add(node)
        visited.append(node)
        
        # Nếu đã đạt tới điểm đích, dừng thuật toán
        if node == goal:
            break
            
        # Duyệt qua các hàng xóm đi được của node hiện tại (né các ô nằm trong tập avoid)
        for nxt in hospital_map.neighbors(node, avoid):
            step = hospital_map.cell_cost(nxt) # Lấy chi phí đi vào ô hàng xóm (sàn = 1, ô trọng số = 5)
            new_cost = cost + step             # Tính chi phí g mới từ start -> node -> nxt
            
            # Nếu tìm thấy một đường đi tốt hơn (hoặc đường đi đầu tiên) tới nxt
            if nxt not in g_score or new_cost < g_score[nxt]:
                g_score[nxt] = new_cost
                parent[nxt] = node
                heuristic = manhattan(nxt, goal) # Ước lượng khoảng cách Manhattan tới đích
                
                # Xác định độ ưu tiên:
                # - Với Greedy: Chỉ quan tâm heuristic h(n)
                # - Với A*: Kết hợp g(n) + h(n) * weight
                priority = heuristic if greedy else new_cost + heuristic * weight
                heapq.heappush(heap, (priority, new_cost, nxt))

    # Tái dựng lại đường đi sau khi tìm kiếm kết thúc
    path = _reconstruct(parent, start, goal)
    return {
        "name": name,
        "path": path,
        "visited": visited,
        "cost": g_score.get(goal, 0),
        "nodes": len(visited),
        "success": bool(path),
    }


def astar_path(hospital_map, start, goal, avoid=None):
    """
    Hàm tìm kiếm đường đi A* giữa 2 điểm.
    Trả về cấu trúc kết quả chuẩn để sử dụng đơn lẻ hoặc làm hàm phụ trợ cho các thuật toán khác.
    """
    return _search(hospital_map, start, goal, "A* Search", avoid=avoid)


def ida_star_path(hospital_map, start, goal, avoid=None, max_iterations=180):
    """
    Thuật toán IDA* (Iterative Deepening A*) tìm đường đi giữa start và goal.
    Kết hợp giữa tìm kiếm theo chiều sâu (DFS) và giới hạn f-limit của A*.
    Tránh bùng nổ bộ nhớ của A* bằng cách không lưu toàn bộ các node trong hàng đợi ưu tiên.
    
    Tham số:
    - max_iterations: Số lần lặp tăng ngưỡng f tối đa để tránh lặp vô hạn.
    """
    avoid = set(avoid or [])
    # Khởi tạo ngưỡng cắt ban đầu là khoảng cách Manhattan từ start đến goal
    threshold = manhattan(start, goal)
    visited = []
    best_path = []
    best_cost = 0
    iterations = 0

    def search(node, g_cost, limit, path, in_path):
        """
        Hàm DFS đệ quy với giới hạn giá trị f_cost = g_cost + h_cost.
        
        Trả về:
        - "FOUND" nếu tìm thấy đích.
        - Giá trị f tối thiểu lớn hơn limit đã gặp để làm ngưỡng cắt tiếp theo.
        """
        nonlocal best_path, best_cost
        f_cost = g_cost + manhattan(node, goal)
        
        # Nếu chi phí vượt quá giới hạn hiện tại, trả về chi phí đó để làm ngưỡng tiếp theo
        if f_cost > limit:
            return f_cost
            
        visited.append(node)
        
        # Tìm thấy đích
        if node == goal:
            best_path = list(path)
            best_cost = g_cost
            return "FOUND"

        next_limit = float("inf")
        # Duyệt qua các hàng xóm đi được
        for nxt in hospital_map.neighbors(node, avoid):
            # Tránh đi vào các node đã nằm trên nhánh DFS hiện tại
            if nxt in in_path:
                continue
            
            in_path.add(nxt)
            path.append(nxt)
            
            # Đệ quy tìm kiếm sâu hơn
            result = search(nxt, g_cost + hospital_map.cell_cost(nxt), limit, path, in_path)
            if result == "FOUND":
                return "FOUND"
            
            # Lưu lại f_cost nhỏ nhất vượt ngưỡng hiện tại để cập nhật threshold
            if result < next_limit:
                next_limit = result
                
            path.pop()
            in_path.remove(nxt)
            
        return next_limit

    # Vòng lặp tăng dần ngưỡng cắt f_limit (threshold)
    while iterations < max_iterations:
        iterations += 1
        result = search(start, 0, threshold, [start], {start})
        
        # Nếu tìm thấy đích, trả về kết quả thành công
        if result == "FOUND":
            return {
                "name": "IDA*",
                "path": best_path,
                "visited": visited,
                "cost": best_cost,
                "nodes": len(visited),
                "success": True,
                "iterations": iterations,
                "final_threshold": threshold,
            }
        # Nếu không còn đường đi nào có thể mở rộng tiếp
        if result == float("inf"):
            break
        # Cập nhật ngưỡng cắt mới bằng giá trị nhỏ nhất vượt ngưỡng cũ
        threshold = result

    # Trả về thất bại nếu hết số vòng lặp hoặc không tìm thấy đường đi
    return {
        "name": "IDA*",
        "path": [],
        "visited": visited,
        "cost": 0,
        "nodes": len(visited),
        "success": False,
        "iterations": iterations,
        "final_threshold": threshold,
    }


def _choose_next(current, tasks):
    """
    Hàm heuristic để chọn nhiệm vụ tiếp theo từ danh sách các nhiệm vụ chưa hoàn thành.
    Sử dụng công thức tính điểm ưu tiên kết hợp giữa:
    - Khoảng cách Manhattan từ vị trí hiện tại đến đích của nhiệm vụ
    - Độ ưu tiên của nhiệm vụ (priority * 3)
    - Trạng thái khẩn cấp (urgent -> giảm đi 8 điểm)
    Nhiệm vụ có điểm số nhỏ nhất sẽ được chọn trước.
    """
    return min(
        tasks,
        key=lambda task: manhattan(current, task.target) - task.priority * 3 + (0 if not task.urgent else -8),
    )


def _route(hospital_map, start, tasks, name, weight=1.0, greedy=False):
    """
    Hàm xây dựng lộ trình đi qua toàn bộ danh sách các nhiệm vụ.
    Ở mỗi bước, robot chọn nhiệm vụ tiếp theo bằng _choose_next và tìm đường đi bằng hàm A* hoặc Greedy.
    """
    started = time.perf_counter()
    current = start
    remaining = list(tasks)
    full_path = []
    full_visited = []
    plan = []
    total_cost = 0

    while remaining:
        # Chọn nhiệm vụ tiếp theo tối ưu nhất
        task = _choose_next(current, remaining)
        # Tìm đường đi từ điểm hiện tại đến nhiệm vụ đã chọn
        result = _search(hospital_map, current, task.target, name, weight=weight, greedy=greedy)
        
        # Nếu không thể tìm đường đi tới nhiệm vụ, dừng và trả về thất bại
        if not result["success"]:
            return _runtime_result(name, started, full_path, plan, total_cost, len(full_visited), False, f"Cannot reach {task.name}.", full_visited)
        
        segment = result["path"]
        # Ghép đoạn đường đi mới vào tổng đường đi (loại bỏ phần tử trùng tại điểm nối)
        full_path = segment if not full_path else full_path + segment[1:]
        full_visited.extend(result["visited"])
        total_cost += result["cost"]
        # Ghi nhận ID của nhiệm vụ vào kế hoạch thực hiện
        plan.append(task.task_id)
        
        # Cập nhật vị trí hiện tại và loại bỏ nhiệm vụ đã được chọn
        current = task.target
        remaining.remove(task)

    return _runtime_result(
        name,
        started,
        full_path,
        plan,
        total_cost,
        len(full_visited),
        True,
        "Route built by distance plus task priority.",
        full_visited,
    )


def _route_with_solver(hospital_map, start, tasks, name, solver):
    """
    Hàm xây dựng lộ trình tương tự _route nhưng sử dụng một solver tìm kiếm tùy chỉnh (ví dụ: IDA*).
    """
    started = time.perf_counter()
    current = start
    remaining = list(tasks)
    full_path = []
    full_visited = []
    plan = []
    total_cost = 0
    total_iterations = 0

    while remaining:
        task = _choose_next(current, remaining)
        # Sử dụng solver (ví dụ: ida_star_path) để tìm đường đi
        result = solver(hospital_map, current, task.target)
        
        if not result["success"]:
            return _runtime_result(
                name,
                started,
                full_path,
                plan,
                total_cost,
                len(full_visited),
                False,
                f"Cannot reach {task.name}.",
                full_visited,
                {"iterations": total_iterations},
            )
        
        segment = result["path"]
        full_path = segment if not full_path else full_path + segment[1:]
        full_visited.extend(result["visited"])
        total_cost += result["cost"]
        total_iterations += result.get("iterations", 0)
        plan.append(task.task_id)
        current = task.target
        remaining.remove(task)

    return _runtime_result(
        name,
        started,
        full_path,
        plan,
        total_cost,
        len(full_visited),
        True,
        "Route built with iterative f-limit deepening.",
        full_visited,
        {"iterations": total_iterations},
    )


def astar_route(hospital_map, start, tasks):
    """
    API ngoài để chạy thuật toán A* xây dựng lộ trình đi qua toàn bộ các bệnh nhân (Level 2).
    """
    return _route(hospital_map, start, tasks, "A* Search", weight=1.0, greedy=False)


def ida_star_route(hospital_map, start, tasks):
    """
    API ngoài để chạy thuật toán IDA* xây dựng lộ trình đi qua toàn bộ các bệnh nhân (Level 2).
    """
    return _route_with_solver(hospital_map, start, tasks, "IDA*", ida_star_path)


def greedy_route(hospital_map, start, tasks):
    """
    API ngoài để chạy thuật toán Greedy Best-First xây dựng lộ trình đi qua toàn bộ các bệnh nhân (Level 2).
    """
    return _route(hospital_map, start, tasks, "Greedy Best-First", weight=1.0, greedy=True)
