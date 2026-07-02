import math
import random
import time

from algorithms.informed import astar_path

# Khởi tạo bộ sinh số ngẫu nhiên với hạt giống (seed) cố định là 42 để đảm bảo kết quả
# chạy thử nghiệm luôn ổn định và có thể tái hiện giống nhau giữa các lần chạy.
RNG = random.Random(42)


def _merge(first, second):
    """
    Hàm phụ trợ ghép nối hai lộ trình tọa độ lại với nhau.
    Loại bỏ phần tử đầu tiên của danh sách thứ hai để tránh lặp lại tọa độ trung gian tại điểm tiếp nối.
    """
    if not first:
        return list(second)
    if not second:
        return list(first)
    return list(first) + list(second)[1:]


def _nearest_charge(hospital_map, pos):
    """
    Hàm tìm kiếm trạm sạc gần vị trí hiện tại (pos) nhất.
    Duyệt qua danh sách các trạm sạc trên bản đồ và sử dụng A* để tìm đường đi ngắn nhất.
    """
    best = None
    for station in hospital_map.charge_stations:
        result = astar_path(hospital_map, pos, station)
        # Chọn trạm sạc có chi phí đường đi (cost) nhỏ nhất
        if result["success"] and (best is None or result["cost"] < best["cost"]):
            best = {
                "station": station,
                "path": result["path"],
                "visited": result["visited"],
                "cost": result["cost"],
                "nodes": result["nodes"],
            }
    return best


def _evaluate(hospital_map, start, tasks, order):
    """
    Hàm đánh giá chất lượng của một thứ tự thực hiện nhiệm vụ (order).
    Tính toán chi tiết quãng đường di chuyển, lượng pin tiêu thụ, số lần sạc pin,
    và điểm số tích lũy (bao gồm cả hình phạt trễ deadline cho các nhiệm vụ khẩn cấp).
    
    Hàm này trả về giá trị "objective" (hàm mục tiêu) để các thuật toán Local Search so sánh.
    """
    current = start
    battery = hospital_map.battery_limit # Lấy giới hạn pin tối đa của robot (ví dụ: 80)
    route = []                           # Lưu trữ toàn bộ lộ trình tọa độ thực tế robot đi
    plan = []                            # Lưu danh sách hành động (tên nhiệm vụ hoặc sạc)
    total_distance = 0
    nodes = 0
    visited = []
    charges = 0                          # Số lần robot phải sạc pin
    score = 0                            # Điểm thưởng tích lũy sau khi làm nhiệm vụ
    elapsed_steps = 0                    # Tổng số bước đi (thời gian trôi qua)
    success = True 
    message = "Plan evaluated."

    # Duyệt qua thứ tự nhiệm vụ được đề xuất
    for index in order:
        task = tasks[index]
        # Tìm đường đi A* trực tiếp từ vị trí hiện tại đến nhiệm vụ
        direct = astar_path(hospital_map, current, task.target)
        nodes += direct["nodes"]
        visited.extend(direct["visited"])
        
        # Nếu không tìm thấy đường đi tới đích trên bản đồ tĩnh
        if not direct["success"]:
            success = False
            message = f"Cannot reach {task.name}."
            break

        # Nếu chi phí di chuyển trực tiếp vượt quá lượng pin hiện có của robot
        if direct["cost"] > battery:
            # Tìm trạm sạc gần vị trí hiện tại nhất
            charge = _nearest_charge(hospital_map, current)
            
            # Nếu không có trạm sạc hoặc lượng pin hiện tại không đủ đi tới trạm sạc đó
            if not charge or charge["cost"] > battery:
                success = False
                message = "Battery cannot reach task or charger."
                break
                
            # robot di chuyển tới trạm sạc trước
            route = _merge(route, charge["path"])
            total_distance += charge["cost"]
            elapsed_steps += charge["cost"]
            nodes += charge["nodes"]
            visited.extend(charge["visited"])
            plan.append("CHARGE")
            charges += 1
            battery = hospital_map.battery_limit # Sạc đầy pin
            current = charge["station"]
            
            # Sau khi sạc xong, tìm lại đường đi từ trạm sạc tới nhiệm vụ
            direct = astar_path(hospital_map, current, task.target)
            nodes += direct["nodes"]
            visited.extend(direct["visited"])
            
            # Nếu vẫn không thể tới được nhiệm vụ hoặc chi phí vượt quá dung lượng pin tối đa
            if not direct["success"] or direct["cost"] > battery:
                success = False
                message = "Task still unreachable after charging."
                break

        # Cập nhật lộ trình sau khi đi đến ô đích của nhiệm vụ thành công
        route = _merge(route, direct["path"])
        total_distance += direct["cost"]
        elapsed_steps += direct["cost"]
        battery -= direct["cost"]
        current = task.target
        plan.append(task.task_id)
        
        # Kiểm tra phạt trễ deadline cho nhiệm vụ khẩn cấp (urgent)
        late_penalty = 50 if task.urgent and task.deadline and elapsed_steps > task.deadline else 0
        score += task.reward + task.priority * 10 - late_penalty

    # Công thức tính giá trị hàm mục tiêu (objective score):
    # Càng nhiều điểm (score) càng tốt, quãng đường càng ngắn càng tốt, càng ít sạc pin càng tốt
    objective = score - total_distance * 2 - charges * 8
    
    # Nếu kế hoạch thất bại (không hoàn thành hết nhiệm vụ), áp dụng hình phạt nặng
    if not success:
        objective -= 500
        
    return {
        "order": list(order),
        "path": route,
        "plan": plan,
        "distance": total_distance,
        "nodes": nodes,
        "visited": visited,
        "charges": charges,
        "score": score,
        "objective": objective,
        "success": success,
        "message": message,
    }


def _neighbors(order):
    """
    Hàm sinh ra các cấu hình lân cận (neighbors) bằng cách đổi chỗ
    hai nhiệm vụ kề nhau trong danh sách thứ tự thực hiện.
    """
    if len(order) < 2:
        return [order]
    items = []
    for i in range(len(order) - 1):
        candidate = list(order)
        # Đổi chỗ 2 phần tử liên tiếp
        candidate[i], candidate[i + 1] = candidate[i + 1], candidate[i]
        items.append(candidate)
    return items


def _finish(name, started, evaluation, iterations):
    """
    Hàm phụ trợ đóng gói kết quả chạy của thuật toán Local Search về dạng chuẩn.
    """
    return {
        "name": name,
        "path": evaluation["path"],
        "plan": evaluation["plan"],
        "cost": evaluation["distance"],
        "path_length": max(0, len(evaluation["path"]) - 1),
        # Tổng số node mở rộng = tổng các node A* + số lượt lặp của thuật toán cục bộ
        "nodes_expanded": evaluation["nodes"] + iterations,
        "runtime_ms": (time.perf_counter() - started) * 1000,
        "success": evaluation["success"],
        "message": evaluation["message"],
        "visited": evaluation.get("visited", evaluation["path"]),
        "score": evaluation["score"],
        "distance": evaluation["distance"],
        "charging_count": evaluation["charges"],
        "objective": round(evaluation["objective"], 2),
    }


def _initial_order(tasks):
    """
    Tạo ra thứ tự thực hiện nhiệm vụ ban đầu (hợp lý hóa ban đầu).
    Sắp xếp các nhiệm vụ tăng dần theo deadline (nếu không có deadline thì coi như vô hạn = 999),
    sau đó giảm dần theo độ ưu tiên (priority).
    """
    return [
        i
        for i, _task in sorted(
            enumerate(tasks),
            key=lambda item: (item[1].deadline or 999, -item[1].priority),
        )
    ]


def simple_hill_climbing(hospital_map, start, tasks):
    """
    Thuật toán Tìm kiếm leo đồi đơn giản (Simple Hill Climbing).
    - Xuất phát từ cấu hình thứ tự ban đầu.
    - Tìm kiếm trong tập lân cận bằng cách đổi chỗ kề nhau.
    - Di chuyển ngay lập tức sang lân cận đầu tiên tốt hơn cấu hình hiện tại (chọn tốt hơn đầu tiên).
    - Dừng khi đạt cực đại địa phương (không lân cận nào tốt hơn) hoặc vượt quá 50 vòng lặp.
    """
    started = time.perf_counter()
    current = _initial_order(tasks)
    best = _evaluate(hospital_map, start, tasks, current)
    iterations = 0

    improved = True
    while improved and iterations < 50:
        improved = False
        # Duyệt qua các thứ tự lân cận
        for candidate_order in _neighbors(current):
            iterations += 1
            candidate = _evaluate(hospital_map, start, tasks, candidate_order)
            
            # Nếu tìm thấy một thứ tự tốt hơn, cập nhật ngay lập tức
            if candidate["objective"] > best["objective"]:
                current = candidate_order
                best = candidate
                improved = True
                break # Thoát vòng lặp để tiếp tục leo đồi từ điểm mới này

    return _finish("Simple Hill Climbing", started, best, iterations)


def local_beam_search(hospital_map, start, tasks, k=3):
    """
    Thuật toán Tìm kiếm chùm cục bộ (Local Beam Search) với độ rộng chùm k=3.
    - Duy trì k trạng thái tốt nhất cùng lúc.
    - Ở mỗi bước, sinh ra tất cả các trạng thái lân cận của tất cả k trạng thái hiện tại.
    - Sắp xếp và chọn ra k trạng thái tốt nhất làm chùm tia mới cho vòng lặp tiếp theo.
    - Dừng lại khi chùm tia không thể cải thiện thêm hoặc đạt tối đa 45 vòng lặp.
    """
    started = time.perf_counter()
    seed = _initial_order(tasks)
    beam_orders = [seed]
    
    # Khởi tạo chùm tia ban đầu chứa các thứ tự lân cận của cấu hình ban đầu cho đến khi đủ k phần tử
    for candidate in _neighbors(seed):
        if candidate not in beam_orders:
            beam_orders.append(candidate)
        if len(beam_orders) >= k:
            break

    # Đánh giá toàn bộ các trạng thái trong chùm tia ban đầu
    beam = [_evaluate(hospital_map, start, tasks, order) for order in beam_orders]
    best = max(beam, key=lambda item: item["objective"])
    iterations = 0

    while iterations < 45:
        candidates = []
        seen_orders = set()
        
        # Sinh toàn bộ lân cận của tất cả các trạng thái trong chùm tia
        for evaluation in beam:
            for order in _neighbors(evaluation["order"]):
                key = tuple(order)
                if key in seen_orders:
                    continue
                seen_orders.add(key)
                candidates.append(_evaluate(hospital_map, start, tasks, order))
                iterations += 1

        if not candidates:
            break
            
        # Sắp xếp các ứng viên lân cận theo hàm mục tiêu giảm dần
        candidates.sort(key=lambda item: item["objective"], reverse=True)
        # Giữ lại k ứng viên tốt nhất làm chùm tia tiếp theo
        next_beam = candidates[:k]
        current_best = next_beam[0]
        
        # Điều kiện dừng: Nếu chùm tia mới không mang lại cải tiến nào tốt hơn best
        # và cấu trúc thứ tự của chùm tia mới hoàn toàn giống với chùm tia cũ.
        if current_best["objective"] <= best["objective"] and all(
            tuple(item["order"]) == tuple(old["order"]) for item, old in zip(next_beam, beam)
        ):
            break
            
        # Cập nhật trạng thái tốt nhất toàn cục
        if current_best["objective"] > best["objective"]:
            best = current_best
        beam = next_beam

    return _finish("Local Beam Search", started, best, iterations)


def simulated_annealing(hospital_map, start, tasks):
    """
    Thuật toán Luyện kim giả lập (Simulated Annealing).
    - Cho phép di chuyển xuống đồi (nhận các trạng thái xấu hơn) với một xác suất nhất định
      để có thể thoát khỏi cực trị địa phương (local optimum).
    - Xác suất nhận trạng thái xấu hơn tính bằng công thức: P = e^(delta / T)
    - Nhiệt độ T giảm dần theo hệ số hạ nhiệt (T_mới = T_cũ * 0.92).
    - Khi nhiệt độ T rất cao, robot khám phá tự do. Khi T nguội dần, nó hội tụ về phía leo đồi thuần túy.
    """
    started = time.perf_counter()
    current_order = _initial_order(tasks)
    current = _evaluate(hospital_map, start, tasks, current_order)
    best = current
    temperature = 40.0 # Khởi tạo nhiệt độ ban đầu
    iterations = 0

    # Vòng lặp chạy cho đến khi nguội lạnh (T <= 0.5) hoặc vượt quá 120 vòng lặp
    while temperature > 0.5 and iterations < 120:
        iterations += 1
        candidate_order = list(current_order)
        
        # Chọn ngẫu nhiên 2 nhiệm vụ để đổi chỗ cho nhau (tạo lân cận ngẫu nhiên)
        a, b = RNG.sample(range(len(candidate_order)), 2)
        candidate_order[a], candidate_order[b] = candidate_order[b], candidate_order[a]
        candidate = _evaluate(hospital_map, start, tasks, candidate_order)
        
        # Tính mức độ chênh lệch chất lượng giữa trạng thái mới và hiện tại
        delta = candidate["objective"] - current["objective"]
        
        # Nếu trạng thái mới tốt hơn (delta > 0), hoặc vượt qua phép thử xác suất của Simulated Annealing:
        if delta > 0 or RNG.random() < math.exp(delta / max(temperature, 0.01)):
            current_order = candidate_order
            current = candidate
            # Cập nhật trạng thái tốt nhất toàn cục
            if current["objective"] > best["objective"]:
                best = current
                
        # Giảm dần nhiệt độ theo cấp số nhân
        temperature *= 0.92

    return _finish("Simulated Annealing", started, best, iterations)
