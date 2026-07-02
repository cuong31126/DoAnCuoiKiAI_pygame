# AI Hospital Dispatcher (Pygame)

**AI Hospital Dispatcher** là dự án mô phỏng và trực quan hóa hệ thống điều phối Robot thông minh trong môi trường bệnh viện (kích thước lưới 20x15). Dự án này tích hợp và trực quan hóa **6 nhóm thuật toán trí tuệ nhân tạo (AI)** khác nhau nhằm giải quyết từ các bài toán tìm đường cơ bản cho đến các bài toán lập kế hoạch phức tạp trong điều kiện bất định, tối ưu hóa pin, giải quyết ràng buộc CSP và ra quyết định đối kháng.

---

## Các Tính Năng Nổi Bật

- **Trực quan hóa thuật toán:** Hiệu ứng loang sóng (wavefront visualization) hiển thị các node đã duyệt (visited nodes) và đường đi tối ưu được tô màu vàng nổi bật.
- **Môi trường mô phỏng trực quan:** Bản đồ lưới hỗ trợ các ô sàn thông thường (cost = 1), ô tường chắn (robot không thể đi qua), ô trọng số nặng (cost = 5), trạm sạc điện, và vật cản di động (dynamic obstacles).
- **Phân tích so sánh hiệu suất:** Cung cấp biểu đồ trực quan (sử dụng `matplotlib` và `numpy`) so sánh thời gian thực thi (`runtime_ms`) và số lượng node đã mở rộng (`nodes_expanded`) giữa các thuật toán trong cùng một nhóm.
- **Hiệu ứng sinh động:** Hỗ trợ âm thanh nền (music), hiệu ứng âm thanh (SFX) và đồ họa sprite chuyển động mượt mà.

---

## Yêu Cầu Hệ Thống & Cài Đặt

### Yêu cầu
- **Python 3.8+**
- Thư viện: **Pygame**, **Matplotlib**, **Numpy**

### Hướng dẫn cài đặt
Cài đặt các thư viện phụ thuộc bằng lệnh sau:
```bash
pip install pygame matplotlib numpy
```

### Khởi chạy chương trình
Chạy tệp tin chính ở thư mục gốc:
```bash
python main.py
```

---

## 📂 Cấu Trúc Thư Mục Dự Án

```text
├── main.py             # Điểm bắt đầu (Entry point) khởi chạy trò chơi
├── settings.py         # Cấu hình chung hệ thống (kích thước grid, màu sắc, FPS, tốc độ...)
├── algorithms/         # Thư mục chứa mã nguồn của các thuật toán AI
│   ├── uninformed.py   # Tìm kiếm mù (BFS, DFS, UCS)
│   ├── informed.py     # Tìm kiếm có Heuristic (A*, IDA*, Greedy Best-First)
│   ├── local_search.py # Tìm kiếm cục bộ (Hill Climbing, Local Beam Search, Simulated Annealing)
│   ├── csp.py          # Lập lịch thỏa mãn ràng buộc (Backtracking, Forward Checking, Min-Conflicts)
│   ├── adversarial.py  # Ra quyết định đối kháng (Minimax, Alpha-Beta, Expectimax)
│   └── complex.py      # Cấu trúc dữ liệu và logic hỗ trợ thuật toán phức tạp
├── core/               # Lõi xử lý logic game, bản đồ, thực thể và UI dùng chung
│   ├── game.py         # Lớp khởi chạy và vòng lặp game chính
│   ├── game_manager.py # Quản lý trạng thái và dữ liệu màn chơi
│   ├── map.py          # Logic xây dựng bản đồ tĩnh và động
│   ├── robot.py        # Logic chuyển động và trạng thái của Robot
│   ├── obstacle.py     # Logic vật cản di động
│   └── algorithm_manager.py # Bộ điều phối thuật toán chung
├── scenes/             # Quản lý các màn hình/cảnh trong game
│   ├── main_menu.py    # Giao diện Menu chính
│   ├── map_select.py   # Giao diện chọn màn chơi/level
│   └── analysis.py     # Giao diện phân tích và vẽ biểu đồ so sánh thuật toán
├── maps/               # Lưu trữ tài nguyên bản đồ và kịch bản mô phỏng
│   └── hospital_dispatcher/
│       └── hospital_scene.py # Quản lý kịch bản chi tiết của từng level
├── assets/             # Hình ảnh (sprites), âm thanh (SFX, Music) và phông chữ
└── README.md           # Tài liệu hướng dẫn sử dụng (tệp tin này)
```

---

## 🎮 Chi Tiết 6 Cấp Độ & Thuật Toán Áp Dụng

Chương trình minh họa 6 bài toán điều phối robot tương ứng với 6 cấp độ:

| Level | Tên Bài Toán | Thuật Toán Triển Khai | Mô Tả & Điều Kiện |
| :--- | :--- | :--- | :--- |
| **Level 1** | **Basic Delivery** | BFS, DFS, UCS | Robot di chuyển từ vị trí xuất phát đến một bệnh nhân duy nhất trên bản đồ tĩnh. |
| **Level 2** | **Multi Patient Delivery** | A* Search, IDA*, Greedy Best-First | Robot phải giao hàng/thuốc đến 4 bệnh nhân khác nhau trên bản đồ tĩnh, sử dụng hàm Heuristic Manhattan để tối ưu hóa quãng đường. |
| **Level 3** | **Battery Optimization** | Simple Hill Climbing, Local Beam Search, Simulated Annealing | Robot xuất phát với lượng pin thấp (30/80) và cần giao hàng cho 4 bệnh nhân. Cần lập lộ trình tối ưu và ghé qua các trạm sạc để nạp năng lượng kịp thời. |
| **Level 4** | **Dynamic Obstacles** | AND-OR Search, Partial Observation, No Observation | Robot tự động lập kế hoạch và di chuyển trong môi trường có vật cản di động tuần hoàn để tránh va chạm. |
| **Level 5** | **Emergency Priority CSP** | Backtracking, Forward Checking, Min-Conflicts | Robot sắp xếp thứ tự thực hiện nhiệm vụ dựa trên độ ưu tiên, deadline của bệnh nhân và giới hạn năng lượng của bản thân sao cho thỏa mãn toàn bộ ràng buộc thời gian. |
| **Level 6** | **Hospital Crisis** | Minimax, Alpha-Beta Pruning, Expectimax | Robot ra quyết định tối ưu trong môi trường khủng hoảng, rủi ro cao (nhiều vật cản di động chặn đường, pin yếu) dựa trên hàm tiện ích (Utility). |

---

## 📊 So Sánh Các Thuật Toán

| Nhóm Thuật Toán | Thuật Toán | Ưu Điểm | Nhược Điểm |
| :--- | :--- | :--- | :--- |
| **Uninformed** | **BFS** | Tìm được đường đi ngắn nhất theo số bước | Mở rộng nhiều node, tốn bộ nhớ |
| | **DFS** | Dễ cài đặt, tốn ít bộ nhớ hơn BFS | Dễ đi vòng, không đảm bảo tối ưu |
| | **UCS** | Đảm bảo tối ưu theo tổng chi phí (cost) | Chậm khi không gian trạng thái lớn |
| **Informed** | **A\*** | Cân bằng hoàn hảo giữa chi phí thực tế và heuristic | Cần thiết kế hàm heuristic tốt |
| | **IDA\*** | Tiết kiệm bộ nhớ vượt trội so với A* | Có thể duyệt lại các trạng thái nhiều lần |
| | **Greedy** | Tìm đường rất nhanh, mở rộng ít node | Không đảm bảo tìm được đường đi tối ưu |
| **Local Search** | **Hill Climbing** | Đơn giản, tính toán nhanh chóng | Dễ bị kẹt tại cực trị địa phương (local optimum) |
| | **Beam Search** | Giữ lại `k` ứng viên tốt nhất, tăng tính ổn định | Tốn chi phí tính toán và đánh giá |
| | **Simulated Annealing** | Có khả năng thoát khỏi cực trị địa phương nhờ xác suất | Phụ thuộc nhiều vào tham số nhiệt độ |
| **Uncertainty** | **AND-OR** | Tạo ra kế hoạch có điều kiện (conditional plan) | Phức tạp khi không gian trạng thái phình to |
| | **Partial Obs** | Thực tế, chỉ quan sát xung quanh robot | Có thể bỏ sót các mối nguy hiểm ở xa |
| | **No Obs** | Minh họa lập kế hoạch trên Belief State | Rất khó tối ưu khi không có thông tin |
| **CSP** | **Backtracking** | Tìm kiếm lời giải chính xác theo đúng ràng buộc | Dễ bị bùng nổ tổ hợp (no nhánh) |
| | **Forward Checking** | Lọc miền giá trị sớm để cắt tỉa nhánh vô nghiệm | Cần hàm nhìn trước (look-ahead) tốt |
| | **Min-Conflicts** | Tìm lời giải cực kỳ nhanh cho các bài toán lớn | Không đảm bảo luôn tìm được lời giải |
| **Adversarial** | **Minimax** | Đưa ra quyết định an toàn nhất trước đối thủ | Duyệt cây rất sâu và tốn tài nguyên |
| | **Alpha-Beta** | Cắt tỉa các nhánh không cần thiết, tăng tốc Minimax | Hiệu quả phụ thuộc vào thứ tự duyệt node |
| | **Expectimax** | Tối ưu hóa trong môi trường có tính ngẫu nhiên | Đòi hỏi mô hình hóa xác suất chính xác |

---

## 📈 Trực Quan Hóa Kết Quả (Analysis Scene)

Sau khi chạy thử nghiệm các thuật toán, bạn có thể truy cập màn hình **Analysis** để xem các biểu đồ trực quan hóa do hệ thống vẽ tự động, so sánh trực tiếp các chỉ số:
1. **Nodes Expanded:** Đo lường độ hiệu quả tìm kiếm (thuật toán nào duyệt ít node hơn sẽ tối ưu hơn).
2. **Runtime (ms):** Thời gian thực thi thực tế của thuật toán trên hệ thống.

---

## 👨‍💻 Thông Tin Repo & Phát Triển

- **Link GitHub:** [DoAnCuoiKiAI_pygame](https://github.com/cuong31126/DoAnCuoiKiAI_pygame.git)
- Dự án được xây dựng và phục vụ cho mục đích học tập, nghiên cứu môn Trí Tuệ Nhân Tạo (AI) ứng dụng trực quan hóa game 2D.
