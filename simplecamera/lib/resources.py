import os
import sys
from pathlib import Path


def get_filename(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        dirname = sys._MEIPASS
    except Exception:
        dirname = str(Path(".").parent.parent.absolute())
    finally:
        path = os.path.join(dirname, relative_path)
    return path
