import os
import warnings

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

warnings.filterwarnings(
    "ignore",
    message="pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module="pygame.pkgdata",
)

from core.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
