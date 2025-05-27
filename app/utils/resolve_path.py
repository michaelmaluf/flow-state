import sys
import os
from pathlib import Path


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Running as PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development - go up to project root
        base_path = Path(__file__).parent.parent.parent

    return str(base_path / relative_path)


def get_script_path(filename):
    return get_resource_path(f'resources/scripts/{filename}')


def get_image_path(filename):
    return get_resource_path(f'resources/images/{filename}')


def get_config_path(filename):
    return get_resource_path(f'resources/config/{filename}')

def get_logs_directory():
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller - use proper macOS location
        logs_dir = Path.home() / "Library" / "Logs" / "FlowState"
    else:
        # Development - keep existing logic
        root_dir = Path(__file__).parent.parent.parent
        logs_dir = root_dir / "logs"

    # Ensure directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    return str(logs_dir)
