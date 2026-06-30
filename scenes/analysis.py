import os
import pygame
import matplotlib
# Use Agg backend for headless image generation to avoid issues inside Pygame's loop
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from core.scene_base import SceneBase
from core.ui import Button, draw_panel, draw_text
from core.map import build_demo_level
from core.algorithm_manager import AlgorithmManager
from settings import (
    COLOR_BG,
    COLOR_GOLD,
    COLOR_WHITE,
    COLOR_GREEN,
    COLOR_RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

class AnalysisScene(SceneBase):
    """Man hinh phan tich so sanh hieu suat 18 thuat toan AI."""

    def __init__(self, screen, game_ref):
        super().__init__(screen, game_ref)
        self.results = []
        self.tab = "TABLE"  # "TABLE", "RUNTIME", "NODES"
        self.runtime_img = None
        self.nodes_img = None
        
        # Base colors matching the hospital scene colors
        self.level_colors = {
            1: (43, 92, 143),     # Blue
            2: (230, 149, 48),    # Orange
            3: (189, 66, 130),    # Pink/Red
            4: (66, 163, 189),    # Cyan
            5: (93, 189, 66),     # Green
            6: (217, 67, 67),     # Bright Red
        }

    def on_enter(self):
        self.game.play_music("assets/sounds/music/menu_theme.mp3")
        self.run_all_algorithms()
        self.generate_static_charts()
        self.load_chart_images()
        self.buttons = self.build_buttons()

    def on_exit(self):
        # Clean up temporary chart images when leaving
        for filename in ("assets/temp_analysis_runtime.png", "assets/temp_analysis_nodes.png"):
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

    def run_all_algorithms(self):
        """Chay 18 thuat toan tren 6 level map va luu ket qua trung binh 10 lan (bo qua lan dau - warmup)."""
        self.results = []
        for level in range(1, 7):
            demo_map = build_demo_level(level)
            manager = AlgorithmManager(demo_map)
            for name in manager.get_algorithms():
                # Chay lan 1 de lay ket qua co ban (duong di, node...) va lam nong (warmup)
                base_res = manager.run_algorithm(name)
                
                # Chay tiep 10 lan de do runtime chuan
                runtimes = []
                for _ in range(10):
                    demo_map.reset()
                    r = manager.run_algorithm(name)
                    runtimes.append(r.get("runtime_ms", 0.0))
                
                # Tinh trung binh cong runtime
                avg_runtime = sum(runtimes) / len(runtimes)
                base_res["runtime_ms"] = avg_runtime
                base_res["name"] = name
                base_res["level"] = level
                self.results.append(base_res)

    def generate_static_charts(self):
        """Ve va luu cac bieu do dung Matplotlib."""
        if not self.results:
            return

        # Setup dark style
        plt.style.use('dark_background')
        
        levels = [r['level'] for r in self.results]
        names = [r['name'] for r in self.results]
        runtimes = [r['runtime_ms'] for r in self.results]
        nodes = [r['nodes_expanded'] for r in self.results]
        
        x = np.arange(len(self.results))
        
        # Color coding list based on level
        bar_colors = []
        for lvl in levels:
            c = self.level_colors.get(lvl, (136, 136, 136))
            bar_colors.append((c[0]/255.0, c[1]/255.0, c[2]/255.0))
            
        short_names = []
        labels_map = {
            "Greedy Best-First": "Greedy",
            "Local Beam Search": "Beam",
            "Simple Hill Climbing": "Hill Climb",
            "Simulated Annealing": "Annealing",
            "AND-OR Search": "AND-OR",
            "Partial Observation": "Partial Obs",
            "No Observation": "No Obs",
            "Backtracking Search": "Backtrack",
            "Forward Checking": "Forward Check",
            "Min-Conflicts": "Conflicts",
            "Alpha-Beta Pruning": "Alpha-Beta"
        }
        for n in names:
            short_names.append(labels_map.get(n, n))
            
        tick_labels = [f"{name}\n(L{lvl})" for name, lvl in zip(short_names, levels)]

        # 1. Bieu do Runtime
        fig, ax = plt.subplots(figsize=(10.5, 4.4), dpi=100)
        fig.patch.set_facecolor('#0f0f23')  # Dong bo mau nen voi COLOR_BG
        ax.set_facecolor('#15162a')
        
        bars = ax.bar(x, runtimes, color=bar_colors, edgecolor='white', linewidth=0.5)
        ax.set_title("THOI GIAN CHAY (ms) CUA 18 THUAT TOAN AI", color='#ffd700', fontsize=13, fontweight='bold', pad=12)
        ax.set_ylabel("Thoi gian (ms)", color='white', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, rotation=35, ha='right', color='white', fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
        
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(f"{h:.2f}",
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 2),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=7, color='white')
                            
        plt.tight_layout()
        plt.savefig('assets/temp_analysis_runtime.png', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()

        # 2. Bieu do Nodes Expanded
        fig, ax = plt.subplots(figsize=(10.5, 4.4), dpi=100)
        fig.patch.set_facecolor('#0f0f23')
        ax.set_facecolor('#15162a')
        
        bars = ax.bar(x, nodes, color=bar_colors, edgecolor='white', linewidth=0.5)
        ax.set_title("SO NODE MO RONG CUA 18 THUAT TOAN AI", color='#ffd700', fontsize=13, fontweight='bold', pad=12)
        ax.set_ylabel("Nodes Expanded", color='white', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, rotation=35, ha='right', color='white', fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
        
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.annotate(f"{int(h)}",
                            xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 2),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=7, color='white')
                            
        plt.tight_layout()
        plt.savefig('assets/temp_analysis_nodes.png', facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()

    def load_chart_images(self):
        """Load bieu do dang anh vao Pygame surface."""
        try:
            if os.path.exists("assets/temp_analysis_runtime.png"):
                self.runtime_img = pygame.image.load("assets/temp_analysis_runtime.png").convert_alpha()
            if os.path.exists("assets/temp_analysis_nodes.png"):
                self.nodes_img = pygame.image.load("assets/temp_analysis_nodes.png").convert_alpha()
        except Exception as e:
            print("Loi load anh bieu do:", e)

    def open_interactive_charts(self):
        """Mo cua so bieu do tuong tac cua Matplotlib."""
        # Hien thi thong bao tren cua so Pygame truoc khi luong bi chan
        self.screen.fill((13, 18, 25))
        
        # Ve thanh thong tin tren
        pygame.draw.rect(self.screen, (25, 25, 50), (0, 0, SCREEN_WIDTH, 68))
        pygame.draw.line(self.screen, (190, 200, 216), (0, 68), (SCREEN_WIDTH, 68), 2)
        draw_text(self.screen, "SO SANH & PHAN TICH HIEU SUAT 18 THUAT TOAN AI", 25, COLOR_GOLD, (30, 18), bold=True)
        
        # Ve khung noi dung thong bao
        content_rect = pygame.Rect(40, 145, 1200, 535)
        draw_panel(self.screen, content_rect, (20, 24, 36), COLOR_WHITE, 230)
        
        draw_text(self.screen, "DANG HIEN THI BIEU DO TUONG TAC...", 28, COLOR_GOLD, (content_rect.centerx, content_rect.centery - 30), center=True, bold=True)
        draw_text(self.screen, "Vui long dong cua so bieu do de tiep tuc tro choi.", 20, COLOR_WHITE, (content_rect.centerx, content_rect.centery + 20), center=True)
        
        # Cap nhat truc tiep len cua so game thuc te
        self.game.window.fill((8, 8, 12))
        scaled = pygame.transform.smoothscale(self.screen, self.game.viewport.size)
        self.game.window.blit(scaled, self.game.viewport.topleft)
        pygame.display.flip()

        # Switch backend to native GUI
        try:
            matplotlib.use('TkAgg', force=True)
            import matplotlib.pyplot as plt
        except Exception:
            try:
                matplotlib.use('Qt5Agg', force=True)
                import matplotlib.pyplot as plt
            except Exception:
                import matplotlib.pyplot as plt
                
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5))
        fig.patch.set_facecolor('#0f0f23')
        
        levels = [r['level'] for r in self.results]
        names = [r['name'] for r in self.results]
        runtimes = [r['runtime_ms'] for r in self.results]
        nodes = [r['nodes_expanded'] for r in self.results]
        x = np.arange(len(self.results))
        
        bar_colors = []
        for lvl in levels:
            c = self.level_colors.get(lvl, (136, 136, 136))
            bar_colors.append((c[0]/255.0, c[1]/255.0, c[2]/255.0))
            
        short_names = []
        labels_map = {
            "Greedy Best-First": "Greedy",
            "Local Beam Search": "Beam",
            "Simple Hill Climbing": "Hill Climb",
            "Simulated Annealing": "Annealing",
            "AND-OR Search": "AND-OR",
            "Partial Observation": "Partial Obs",
            "No Observation": "No Obs",
            "Backtracking Search": "Backtrack",
            "Forward Checking": "Forward Check",
            "Min-Conflicts": "Conflicts",
            "Alpha-Beta Pruning": "Alpha-Beta"
        }
        for n in names:
            short_names.append(labels_map.get(n, n))
            
        tick_labels = [f"{name} (L{lvl})" for name, lvl in zip(short_names, levels)]
        
        # Ax1: Runtime
        ax1.set_facecolor('#15162a')
        bars1 = ax1.bar(x, runtimes, color=bar_colors, edgecolor='white', linewidth=0.5)
        ax1.set_title("Runtime (ms) Comparison", color='#ffd700', fontsize=12, fontweight='bold')
        ax1.set_ylabel("ms", color='white')
        ax1.set_xticks(x)
        ax1.set_xticklabels(tick_labels, rotation=45, ha='right', color='white', fontsize=9)
        ax1.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
        
        # Add labels on top of bars
        for bar in bars1:
            h = bar.get_height()
            if h > 0:
                ax1.annotate(f"{h:.1f}", xy=(bar.get_x() + bar.get_width()/2, h),
                             xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=8, color='white')

        # Ax2: Nodes
        ax2.set_facecolor('#15162a')
        bars2 = ax2.bar(x, nodes, color=bar_colors, edgecolor='white', linewidth=0.5)
        ax2.set_title("Nodes Expanded Comparison", color='#ffd700', fontsize=12, fontweight='bold')
        ax2.set_ylabel("Nodes count", color='white')
        ax2.set_xticks(x)
        ax2.set_xticklabels(tick_labels, rotation=45, ha='right', color='white', fontsize=9)
        ax2.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
        
        for bar in bars2:
            h = bar.get_height()
            if h > 0:
                ax2.annotate(f"{int(h)}", xy=(bar.get_x() + bar.get_width()/2, h),
                             xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=8, color='white')

        plt.suptitle("AI HOSPITAL DISPATCHER - 18 ALGORITHMS ANALYTICS", color='white', fontsize=15, fontweight='bold')
        plt.tight_layout()
        
        # Show interactive matplotlib window (blocks pygame update)
        plt.show()
        
        # Re-set Agg backend to keep static generation clean
        matplotlib.use('Agg', force=True)

    def build_buttons(self):
        buttons = [
            Button((40, 90, 160, 36), "BANG SO LIEU", lambda: self.set_tab("TABLE"), 
                   (42, 130, 96) if self.tab == "TABLE" else (55, 83, 132), 
                   (66, 170, 126) if self.tab == "TABLE" else (78, 115, 178), 14),
            Button((210, 90, 200, 36), "BIEU DO RUNTIME", lambda: self.set_tab("RUNTIME"), 
                   (42, 130, 96) if self.tab == "RUNTIME" else (55, 83, 132), 
                   (66, 170, 126) if self.tab == "RUNTIME" else (78, 115, 178), 14),
            Button((420, 90, 200, 36), "BIEU DO NODES", lambda: self.set_tab("NODES"), 
                   (42, 130, 96) if self.tab == "NODES" else (55, 83, 132), 
                   (66, 170, 126) if self.tab == "NODES" else (78, 115, 178), 14),
            Button((630, 90, 240, 36), "MO BIEU DO TUONG TAC", self.open_interactive_charts, 
                   (80, 50, 120), (110, 75, 160), 14),
            Button((1100, 90, 140, 36), "TRO VE", lambda: self.finish("main_menu"), 
                   (132, 48, 56), (178, 68, 78), 15),
        ]
        return buttons

    def set_tab(self, tab):
        self.tab = tab
        self.buttons = self.build_buttons()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.finish("main_menu")
                return
            for button in self.buttons:
                if button.handle_event(event):
                    break

    def update(self, dt):
        pass

    def draw(self):
        # 1. Background
        self.screen.fill((13, 18, 25))
        
        # 2. Top bar
        pygame.draw.rect(self.screen, (25, 25, 50), (0, 0, SCREEN_WIDTH, 68))
        pygame.draw.line(self.screen, (190, 200, 216), (0, 68), (SCREEN_WIDTH, 68), 2)
        draw_text(self.screen, "SO SANH & PHAN TICH HIEU SUAT 18 THUAT TOAN AI", 25, COLOR_GOLD, (30, 18), bold=True)
        
        # Draw buttons
        for btn in self.buttons:
            btn.draw(self.screen)
            
        # 3. Content Panel
        content_rect = pygame.Rect(40, 145, 1200, 535)
        draw_panel(self.screen, content_rect, (20, 24, 36), COLOR_WHITE, 230)
        
        if self.tab == "TABLE":
            self.draw_table_view(content_rect)
        elif self.tab == "RUNTIME" and self.runtime_img:
            img_rect = self.runtime_img.get_rect(center=content_rect.center)
            self.screen.blit(self.runtime_img, img_rect)
        elif self.tab == "NODES" and self.nodes_img:
            img_rect = self.nodes_img.get_rect(center=content_rect.center)
            self.screen.blit(self.nodes_img, img_rect)

    def draw_table_view(self, rect):
        """Ve bang thong ke 18 thuat toan trong pygame."""
        # Headers & Positions
        headers = ["STT", "Lvl", "Thuat Toan", "Duong Di", "Chi Phi", "Node Duyet", "Time (ms)", "K.Qua"]
        col_xs = [rect.x + 20, rect.x + 80, rect.x + 140, rect.x + 390, rect.x + 520, rect.x + 650, rect.x + 790, rect.x + 920]
        
        # Draw Header Row
        header_y = rect.y + 15
        pygame.draw.rect(self.screen, (34, 45, 68), (rect.x + 8, header_y - 4, rect.width - 16, 32), border_radius=4)
        for x, header in zip(col_xs, headers):
            draw_text(self.screen, header, 15, COLOR_GOLD, (x, header_y), bold=True)
            
        # Draw Rows
        row_height = 24
        start_y = rect.y + 50
        
        for i, res in enumerate(self.results):
            row_y = start_y + i * row_height
            
            # Alternating row background for readability
            if i % 2 == 0:
                pygame.draw.rect(self.screen, (24, 30, 48), (rect.x + 8, row_y - 2, rect.width - 16, row_height), border_radius=4)
                
            status_color = COLOR_GREEN if res.get("success") else COLOR_RED
            status_text = "SUCCESS" if res.get("success") else "FAILED"
            
            # Level color badge
            lvl = res.get("level", 1)
            lvl_color = self.level_colors.get(lvl, COLOR_WHITE)
            
            row_data = [
                str(i + 1),
                f"L{lvl}",
                res.get("name", ""),
                str(res.get("path_length", 0)),
                str(round(res.get("cost", 0), 1)),
                str(res.get("nodes_expanded", 0)),
                f"{res.get('runtime_ms', 0):.2f}",
                status_text
            ]
            
            for col_idx, (x, val) in enumerate(zip(col_xs, row_data)):
                # Custom colors for columns
                if col_idx == 1:
                    color = lvl_color # huhu 
                elif col_idx == 2:
                    color = COLOR_GOLD
                elif col_idx == 7:
                    color = status_color
                else:
                    color = COLOR_WHITE
                    
                draw_text(self.screen, val, 14, color, (x, row_y), bold=(col_idx in (1, 2, 7)))
