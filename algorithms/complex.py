import time
# Import các hàm dùng chung từ file common.py trong cùng thư mục
from .informed import _search, _runtime_result, manhattan


# lập kế hoạch dự phòng ( contingency plan ) dựa trên các tình huống giả định của vật cản động 
def and_or_search(hospital_map, start, goal):
    started = time.perf_counter()
    # đưa ra 3 kịch bản di chuyển của vật cản  sau vị trí hiện tại , 2 bước và 5 bước 
    # đây là các nút and , môi trườn đưa ra tình huống 
    scenarios = [
        hospital_map.dynamic_positions(),
        hospital_map.predicted_dynamic_positions(steps=2),
        hospital_map.predicted_dynamic_positions(steps=5),
    ]
    # hợp nhất các ô nguy hiểm trong 3 kịch bản thành 1 tập hợp avoid 
    avoid = set().union(*scenarios) 
    # gọi A* tìm đường an taons tránh các ô avoid 
    # . đây là quyết đinh của robot - nut or robot chọn hd tối ưu 
    result = _search(hospital_map, start, goal, "AND-OR Search", avoid=avoid)
    conditional_plan = {
        "or_node": "choose next robot move with lowest f = g + h",
        "and_nodes": len(scenarios),
        "avoided_cells": len(avoid),
    }
    # đóng gói kt thuật toán trả vè UI 
    return _runtime_result(
        "AND-OR Search",
        started,
        result["path"],
        ["conditional_plan"],
        result["cost"],
        result["nodes"] + len(scenarios), # số node tiêutoons + thêm 3 ghi nhận cho 3 kịch bản 
        result["success"],
        "Builds a conditional plan over predicted obstacle outcomes.",
        result["visited"],
        {"conditional_plan": conditional_plan, "replan_count": 0, "collision_count": 0},
    )



# robot chỉ nhìn thấy vật cản trong tầm nhìn radar ( 4 ô ) xung quanh nó 
def partial_observation_search(hospital_map, start, goal):
    started = time.perf_counter()
    # lấy phép giao giữa vvậtcanr động và các ô robot nhìn thấy 
    # hospital_map.dynamic_positions(): Tập hợp tọa độ  (ví dụ: xe đẩy y tá, bệnh nhân đi lại).
    #hospital_map.visible_cells(start): Tập hợp tất cả các ô trên lưới mà Robot có thể nhìn thấy
    visible_dynamic = hospital_map.dynamic_positions() & hospital_map.visible_cells(start)
    # robot chỉ tránh nhg vật cản trong tầm mắt và gọi A* tìm đương tránh các vật cản 
    result = _search(
        hospital_map,
        start,
        goal,
        "Partial Observation",
        avoid=visible_dynamic,
    )
    # đogs gói kq tìm kiếm , khi chạy thực tế robot di chuyển và nhìn thấy vật cản mới 
    # hệ thống ui sẽ tự kích hoạt lại thuật toán 
    return _runtime_result(
        "Partial Observation",
        started,
        result["path"],
        [],
        result["cost"],
        result["nodes"],
        result["success"],
        "Plans with only nearby moving obstacles treated as known.",
        result["visited"],
        {"replan_count": 0, "collision_count": 0, "vision_radius": hospital_map.vision_radius},
    )




# hàm trợ giúp trạng thái niềm tin ( dự đoán tập hợp các vị trí khả thi khi thực hiện hành động di chuyển )
def _belief_after_action(hospital_map, belief, action):
    dr, dc = action
    next_belief = set()
    
    for row, col in belief:
        nxt = (row + dr, col + dc)
        # nếu nxt là tường robot đứng yên tại vt cũ 
        # đọc them file hospital_map đê 
        next_belief.add(nxt if hospital_map.passable(nxt) else (row, col))
    return next_belief



# bài toán robot bị mù hoàn toàn .
# phải thực hiện 1 chuỗi hd ép buộc coercion dể tự đưa mình vào 1 vt xác định 

def no_observation_search(hospital_map, start, goal):
    started = time.perf_counter()
    # khởi tạo trang jthais niem tin ban dau 
    # gia dinh có thẻ đang dứng ở bat ky o trong nào tren ban do 
    belief = {
        (row, col)
        for row in range(hospital_map.rows)
        for col in range(hospital_map.cols)
        if hospital_map.passable((row, col))
    }
    # khởi tạo ds 4 hướng di chuyển và các biến lưu vết 
    actions = [(-1, 0), (0, -1), (1, 0), (0, 1)]
    coercion = []
    belief_trace = []
    # thực hiện tối đa 40 bước ép buộc để thu hẹp tập hợp các vị trí khả thi

    for _ in range(40):
        if len(belief) <= 1:
            break
        # vs mỗi hướng tính thử xem nếu đi hướng đó thì tập vị trí khả thi belief sẽ co hẹp lại còn bao nhiêu ô 

        candidates = [(_belief_after_action(hospital_map, belief, action), action) for action in actions]
        next_belief, action = min(candidates, key=lambda item: len(item[0]))
        if len(next_belief) >= len(belief):
            break
        belief = next_belief
        coercion.append(action)
        # lấy 12 ô vẽ màu xám giả định vẽ trên UI dồn dần chỉ còn lại 1 ô 
        belief_trace.extend(list(belief)[:12])

    # dự đoán trc vị trí vật cản động ở 3 bước tiếp theo 
    avoid = hospital_map.predicted_dynamic_positions(steps=3)
    result = _search(hospital_map, start, goal, "No Observation", avoid=avoid)
    visited = belief_trace + result["visited"]
    return _runtime_result(
        "No Observation",
        started,
        result["path"],
        ["coercion"] + [str(action) for action in coercion],
        result["cost"],
        result["nodes"] + len(belief_trace),
        result["success"],
        "Uses a blind belief state, then follows a robust route to the goal.",
        visited,
        {"belief_size": len(belief), "vision_radius": 0, "coercion_steps": len(coercion)},
    )
