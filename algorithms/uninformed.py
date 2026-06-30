from collections import deque
import heapq
import time

# đóng gói kết qẩu 
def _result(name, path, visited, cost, success=True, message="Done"):
    return {
        "name": name,
        "path": path,   # ds các ô tọa độ tạo thành đường đi 
        "plan": [],
        "cost": cost,  # tổng chi phí di chuyển 
        "path_length": max(0, len(path) - 1),
        "nodes_expanded": len(visited),   # số ô thuật toán duyệt qua 
        "runtime_ms": 0.0,   # thời gian chạy 
        "success": success and bool(path),  # trạng thái thành công 
        "message": message,  # thông báo status 
        "visited": visited, # thứ tự các ô đc duyệt 
    }


# lần vết đường đi 
def _reconstruct(parent, start, goal):
    if goal not in parent and goal != start:
        return []
    node = goal
    path = [node]
    while node != start:
        node = parent[node]
        path.append(node)
    path.reverse()
    return path

# tính thời gian chạy 
def _with_runtime(result, started):
    result["runtime_ms"] = (time.perf_counter() - started) * 1000
    return result

# BFS sử dụng queue FIFO , 
def bfs_search(hospital_map, start, goal):
    started = time.perf_counter()  # ghi lại tg bắt đầu 
    queue = deque([start])  # khởi tạo hàng đợi chứa điểm xuất phát 
    parent = {start: start}  # ép start có cha là chính nó 
    visited = [] 

    while queue:
        node = queue.popleft()  # lấy ptu đầu ra 
        visited.append(node)   # đánh dẫu đã duyệt 
        if node == goal:
            break
        for nxt in hospital_map.neighbors(node): # xét các ô hàng xóm đi đc xung quanh 
            if nxt not in parent:  # nếu chua từng đc xếp 
                parent[nxt] = node # ghi nhận cha của nxxt là node hiện tại 
                queue.append(nxt) # thêm ô vào cuối hàng dợi 

    path = _reconstruct(parent, start, goal) # dựng lại đường đi 
    message = "BFS found the shortest path by number of steps." if path else "BFS could not reach the task."
    return _with_runtime(_result("BFS", path, visited, max(0, len(path) - 1), bool(path), message), started)

# def bfs_search(hospital_map, start, goal):
#     started = time.perf_counter()
    
#     # Trường hợp đặc biệt: điểm xuất phát chính là đích
#     if start == goal:
#         return _with_runtime(_result("BFS", [start], [start], 0, True, "BFS found the path."), started)

#     queue = deque([start])
#     parent = {start: start}
#     visited = []

#     while queue:
#         node = queue.popleft()
#         visited.append(node)
        
#         # KHÔNG kiểm tra goal ở đây nữa
        
#         for nxt in hospital_map.neighbors(node):
#             if nxt not in parent:
#                 parent[nxt] = node
                
#                 # KIỂM TRA ĐÍCH SỚM TẠI ĐÂY 🎯
#                 if nxt == goal:
#                     # Vì nxt là đích, ta thêm luôn nxt vào visited để ghi nhận đã tìm thấy
#                     visited.append(nxt)
#                     queue.clear() # Xóa queue để thoát vòng lặp while nhanh chóng
#                     break
                    
#                 queue.append(nxt)

#     path = _reconstruct(parent, start, goal)
#     message = "BFS found the shortest path by number of steps." if path else "BFS could not reach the task."
#     return _with_runtime(_result("BFS", path, visited, max(0, len(path) - 1), bool(path), message), started)



# DFS KHÔNG có cơ chế tìm đường ngắn nhất. 
# Cái đường đi (path) mà thuật toán này trả về đơn thuần là nhánh cây đầu tiên 
# chạm được vào goal trong quá trình nó đâm sâu xuống các ô.
def dfs_search(hospital_map, start, goal, max_depth=90):
    started = time.perf_counter()
    stack = [(start, [start])]
    visited = []
    seen = set()
    path = []

    while stack:
        node, current_path = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        visited.append(node)
        if node == goal:
            path = current_path
            break
        if len(current_path) > max_depth:
            continue
        for nxt in reversed(list(hospital_map.neighbors(node))):
            if nxt not in seen:
                stack.append((nxt, current_path + [nxt]))

    message = "DFS found a path using depth-first exploration." if path else "DFS depth limit reached before success."
    return _with_runtime(_result("DFS", path, visited, max(0, len(path) - 1), bool(path), message), started)


# Thuật toán UCS (Uniform Cost Search -
#  Tìm kiếm chi phí đồng nhất) chính là phiên bản mở rộng của BFS n
def ucs_search(hospital_map, start, goal):
    started = time.perf_counter()
    heap = [(0, start)]  # khởi tạo 1 ds đóng vai trò làm min-heap , chi phí tích lũy ,tọa độ 
    parent = {start: start} 
    cost_so_far = {start: 0}
    visited = []
    closed = set()

    while heap:
        cost, node = heapq.heappop(heap) # tìm và rút ra ô node có giá trị cost nhỏ nhất 
        if node in closed:
            continue
        closed.add(node)
        visited.append(node)
        if node == goal:
            break
        # mở rộng vòng lặp và tính chi phí hàng xóm 
        for nxt in hospital_map.neighbors(node):
            # tính tổng chi phí mới từ start qua node hiện tại -> tới ô hàng xóm nxt 
            new_cost = cost + hospital_map.cell_cost(nxt)
            # đk cập nhật 
            # ô hàng xóm nxt chua bao h đc duyệtqua hoặc ô này rẻ hơn con đường cũ 
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                parent[nxt] = node
                heapq.heappush(heap, (new_cost, nxt)) # đẩy tuple chứa chi phí mới và tạo đọ ô nxt vào heap để nó xếp hàng chờ duyệt 
                

    path = _reconstruct(parent, start, goal)
    message = "UCS minimized weighted cell cost." if path else "UCS could not reach the task."
    return _with_runtime(_result("UCS", path, visited, cost_so_far.get(goal, 0), bool(path), message), started)

