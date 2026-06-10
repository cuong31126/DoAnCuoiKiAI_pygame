import os
import sys
# os và sys thư viện xử lý đường dẫn tệp tin và thoát chương trình, được sử dụng trong việc quản lý tài nguyên và kết thúc trò chơi.
import pygame

from core.ui import assets, set_ui_mouse_pos  # hàm cập nhật vị trí chuột 
from settings import COLOR_BG, FPS, MUSIC_VOLUME, SCREEN_HEIGHT, SCREEN_WIDTH # các hằng số cài đặt từ file cấu hình riêng 
# tốc độ khung hình , âm lượng , kích thước màn hình 

class Game:
    """Quan ly cua so, vong lap chinh va chuyen scene."""

    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass 
        # tránh âm thanh lỗi lm game bị sập 

        pygame.display.set_caption("AI Hospital Dispatcher") # đặt tiêu đề cho cửa sổ 
        self.window = pygame.display.set_mode(self.compute_window_size(), pygame.RESIZABLE) # tạo cửa sổ tính toán tự động và tự kéo giãn đc 
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha() # tạo bề mặt ảo vs size cố định 
        self.viewport = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.update_viewport() # gọi hàm tính toán lại vùng nhìn để đảm bảo tỉ lệ khung hình chuẩn 
        self.clock = pygame.time.Clock() # bộ đếm tg giúp kiếm soát FPS 
        self.running = True  # biến cờ , nếu là True thì game tiếp tục chạy , False thì dừng 
        self.scene = None
        self.change_scene("main_menu") # chuyển phân cảnh đầutieen của game thành menu chính 

# hàm tính toán tỉ lệ màn hình 
    def compute_window_size(self):
        info = pygame.display.Info()
        max_w = max(960, info.current_w - 80)
        max_h = max(540, info.current_h - 120)
        scale = min(max_w / SCREEN_WIDTH, max_h / SCREEN_HEIGHT, 1.0)
        return (max(960, int(SCREEN_WIDTH * scale)), max(540, int(SCREEN_HEIGHT * scale)))

# hàm tính toán vùng hiển thị để đảm bảo tỉ lệ khung hình chuẩn khi cửa sổ được thay đổi kích thước
    def update_viewport(self):
        win_w, win_h = self.window.get_size()
        scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
        render_w = max(1, int(SCREEN_WIDTH * scale))
        render_h = max(1, int(SCREEN_HEIGHT * scale))
        offset_x = (win_w - render_w) // 2
        offset_y = (win_h - render_h) // 2
        self.viewport = pygame.Rect(offset_x, offset_y, render_w, render_h)

# chuẩn hóa tọa độ chuột 
    def map_mouse_pos(self, pos):
        if not self.viewport.collidepoint(pos):
            return (-9999, -9999) # nếu chuột nằm ngoài thì để số này 
        x, y = pos
        rel_x = (x - self.viewport.x) / self.viewport.width
        rel_y = (y - self.viewport.y) / self.viewport.height
        return (int(rel_x * SCREEN_WIDTH), int(rel_y * SCREEN_HEIGHT))

# có sự kiện về chuột thay thế tọa độ chuột thức tế qua hàm map mouse pos để đảm bảo tương thích với vùng hiển thị đã được tính toán , đồng thời xử lý sự kiện thay đổi kích thước cửa sổ để cập nhật lại vùng nhìn
    def normalize_events(self, events):
        mapped = []
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                self.update_viewport()
                continue
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                event_dict = event.dict.copy()
                event_dict["pos"] = self.map_mouse_pos(event.pos)
                mapped.append(pygame.event.Event(event.type, event_dict))
            else:
                mapped.append(event)
        return mapped

# quản lý chuyển đổi scene 
    def change_scene(self, scene_name):
        # Chuyen sang scene phu hop theo ten scene/level
        if self.scene:
            self.scene.on_exit()

        if scene_name == "main_menu":
            from scenes.main_menu import MainMenu

            self.scene = MainMenu(self.screen, self)
        elif scene_name == "map_select":
            from scenes.map_select import MapSelect

            self.scene = MapSelect(self.screen, self)
        elif scene_name.startswith("map") and scene_name[3:].isdigit():
            from maps.hospital_dispatcher.hospital_scene import HospitalScene

            self.scene = HospitalScene(self.screen, self, int(scene_name[3:]))
        else:
            raise ValueError(f"Scene khong ton tai: {scene_name}")

        self.scene.on_enter() # kích hoạt thiết lập ban đầu khi bước vào scene mới 

# trình phát nhạc nền với khả năng xử lý lỗi nếu thư viện âm thanh không được khởi tạo hoặc tệp tin âm thanh không tồn tại, đảm bảo rằng trò chơi vẫn hoạt động mượt mà ngay cả khi có vấn đề với âm thanh.
    def play_music(self, path, loops=-1, volume=MUSIC_VOLUME):
        if not pygame.mixer.get_init():
            return
        resolved = assets.resolve(path)
        if not os.path.exists(resolved):
            return
        try:
            pygame.mixer.music.load(resolved)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops)
        except pygame.error:
            pass

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def quit(self):
        self.running = False

# vòng lặp game chính 
    def run(self):
        # Vong lap chinh: nhan su kien, cap nhat scene, va ve len cua so
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            raw_events = pygame.event.get()
            for event in raw_events:
                if event.type == pygame.QUIT: # nếu ng dùng bấm dấu x 
                    self.running = False
            events = self.normalize_events(raw_events)
            set_ui_mouse_pos(self.map_mouse_pos(pygame.mouse.get_pos()))

            if self.scene:
                self.scene.handle_events(events) # truyền các sự biện vào cho scene xử lý 
                self.scene.update(dt) # cập nhật logic 
                self.screen.fill(COLOR_BG) # xóa màn hình ảo cữ bằng màu nền 
                self.scene.draw()
                if self.scene.finished:
                    next_scene = self.scene.next_scene
                    self.scene.finished = False
                    self.change_scene(next_scene)

            self.window.fill((8, 8, 12))
            scaled = pygame.transform.smoothscale(self.screen, self.viewport.size)
            self.window.blit(scaled, self.viewport.topleft) # vẽ màn hình ảo sau khi co giãn lên trên cửa sổ tht tại vị trí góc trên bên trái 
            pygame.display.flip()

        if self.scene:
            self.scene.on_exit()
        pygame.quit()
        sys.exit()
