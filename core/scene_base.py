from abc import ABC


class SceneBase(ABC):
    """Lop co so cho moi man hinh trong game."""

    def __init__(self, screen, game_ref):
        self.screen = screen
        self.game = game_ref
        self.finished = False
        self.next_scene = None

    def on_enter(self):
        """Ham goi khi scene bat dau."""

    def on_exit(self):
        """Ham goi khi scene ket thuc."""

    def handle_events(self, events):
        """Xu ly danh sach su kien pygame."""

    def update(self, dt):
        """Cap nhat logic theo dt tinh bang giay."""

    def draw(self):
        """Ve scene len screen."""

    def finish(self, next_scene):
        """Bao cho game doi sang scene tiep theo."""
        self.finished = True
        self.next_scene = next_scene
