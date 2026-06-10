# AI Hospital Dispatcher

AI Hospital Dispatcher la game mo phong AI bang Pygame. Nguoi choi dieu khien robot trong benh vien, chon thuat toan phu hop cho tung man va quan sat cach agent lap ke hoach, tim duong, cap nhat theo moi truong dong.

## Yeu cau

- Python 3.12 hoac tuong duong
- Cac thu vien trong `requirements.txt`

## Cai dat

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Chay game

```powershell
python main.py
```

## Kiem thu

```powershell
python -m unittest discover
```

## Dieu khien chinh

- `BAT DAU`: vao man choi
- `CHON MAN`: mo danh sach level
- `RUN`: chay thuat toan dang chon
- `ANALYZE`: so sanh cac thuat toan trong man hien tai
- `RESET`: choi lai level hien tai
- `LEVELS`: quay ve man chon level
- `MENU`: quay ve menu chinh
- `ESC`: dong bang phan tich hoac thoat hop thoai xac nhan

## PEAS cua agent

### Muc tieu chung

Agent la robot cuu ho y te. Nhiem vu la di chuyen qua luoi, thuc hien nhiem vu dung thu tu, toi uu duong di va tranh het nang luong / het thoi gian.

### P1. Level 1 - Basic Delivery

- Performance: den muc tieu bang it buoc, it cost, khong bi chan, hoan thanh dung duong di
- Environment: luoi co tuong, o trong, duong di co trong so
- Actuators: di len / xuong / trai / phai, dung, reset, mo menu
- Sensors: vi tri hien tai, gia tri o luoi, duong da mo phong, trang thai nhiem vu

### P2. Level 2 - Multi Patient Delivery

- Performance: tim duong toi uu de thu thap / phan phoi nhieu muc tieu
- Environment: nhieu task, nhieu chi phi o, co tram sac
- Actuators: di chuyen, chon thuat toan A*, Greedy, Weighted A*
- Sensors: vi tri robot, danh sach task con lai, cost tung o, tram sac

### P3. Level 3 - Battery Optimization

- Performance: hoan thanh tat ca task truoc khi het pin
- Environment: luoi co pin gioi han, phai quay ve tram sac khi can
- Actuators: di chuyen, sac pin, reset
- Sensors: pin hien tai, khoang cach den task, vi tri tram sac

### P4. Level 4 - Dynamic Obstacles

- Performance: hoan thanh nhiem vu trong moi truong dong, re-plan khi co vat can
- Environment: co vat can di dong, tam nhin gioi han, duong di thay doi
- Actuators: di chuyen, lap ke hoach lai, reset
- Sensors: vi tri robot, vi tri vat can dong, duong hien tai, tam nhin

### P5. Level 5 - Emergency Priority CSP

- Performance: uu tien nhiem vu gap, dap ung deadline, giam vi pham rang buoc
- Environment: nhieu task co deadline, co uu tien khac nhau
- Actuators: sap xep thu tu task, di chuyen, phan tich rang buoc
- Sensors: deadline, priority, route cost, task completed / uncompleted

### P6. Level 6 - Hospital Crisis

- Performance: chon hanh dong tot nhat trong tinh huong doi khang / bat dinh
- Environment: cac tinh huong can quyet dinh gan giong game search
- Actuators: chon chien luoc, di chuyen, re-plan
- Sensors: trang thai hien tai, loi ich uoc luong, rui ro, ket qua mo phong

## Thuat toan theo level

- Level 1: BFS, DFS, UCS
- Level 2: A* Search, Greedy Best-First, Weighted A*
- Level 3: Simple Hill Climbing, Stochastic Hill Climbing, Simulated Annealing
- Level 4: Online Re-planning A*, Partial Observation, Constraint Propagation
- Level 5: Backtracking Search, Min-Conflicts, Constraint Graph
- Level 6: Minimax, Alpha-Beta Pruning, Expectimax

## Cau truc thu muc

```text
main.py                 Entry point
settings.py             Cau hinh man hinh, mau sac, toc do, duong dan
core/                   Game loop, scene base, UI, animation, manager
algorithms/             Cac thuat toan AI
scenes/                 Menu chinh va man chon level
maps/                   Logic man choi
ui/                     HUD va thanh phan giao dien
assets/                 Hinh anh, am thanh, font
tests/                  Unit test
```

## Ghi chu

- Project da co san asset benh vien trong `assets/benhvien/`.
- `README.md` nay tap trung vao mo ta co cau, PEAS va cach chay game.
