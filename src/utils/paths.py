import os
import sys


def get_assets_path():
    if getattr(sys, "frozen", False):
        # Estamos no executável PyInstaller
        return os.path.join(sys._MEIPASS, "assets")
    else:
        # Desenvolvimento
        return "src/assets"
