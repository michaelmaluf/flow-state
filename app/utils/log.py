import logging
import logging.config
import logging.handlers
import os
import shutil
import sys

import yaml

from app.utils.resolve_path import get_config_path, get_logs_directory


class LevelOnlyFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = getattr(logging, level) if isinstance(level, str) else level

    def filter(self, record):
        return record.levelno == self.level


class LevelEqualOrAboveFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = getattr(logging, level) if isinstance(level, str) else level

    def filter(self, record):
        return record.levelno >= self.level


class LevelInRangeFilter(logging.Filter):
    def __init__(self, min_level, max_level):
        super().__init__()
        self.min_level = getattr(logging, min_level) if isinstance(min_level, str) else min_level
        self.max_level = getattr(logging, max_level) if isinstance(max_level, str) else max_level

    def filter(self, record):
        return self.min_level <= record.levelno <= self.max_level

def register_logging_filters():
    module = sys.modules['__main__']
    module.LevelOnlyFilter = LevelOnlyFilter
    module.LevelEqualOrAboveFilter = LevelEqualOrAboveFilter
    module.LevelInRangeFilter = LevelInRangeFilter

def setup_logging(default_path='log.yaml', default_level=logging.INFO):
    """Setup logging configuration"""
    try:
        register_logging_filters()

        logs_dir = get_logs_directory()
        config_path = get_config_path(default_path)

        # Create logs directory
        os.makedirs(logs_dir, exist_ok=True)

        if os.path.exists(config_path):
            # Load config
            with open(config_path, 'rt') as f:
                config = yaml.safe_load(f.read())

            # Fix log file paths
            for handler in config.get('handlers', {}).values():
                if 'filename' in handler:
                    filename = handler['filename']
                    if filename.startswith('logs/'):
                        handler['filename'] = os.path.join(logs_dir, os.path.basename(filename))
                    elif not os.path.isabs(filename):
                        handler['filename'] = os.path.join(logs_dir, filename)

            logging.config.dictConfig(config)
            print(f"Logging configured from {config_path}")
        else:
            # Default config
            print(f"Config file not found at {config_path}. Using basic configuration.")
            logging.basicConfig(level=default_level)
    except Exception as e:
        print(f"Error setting up logging: {e}")
        import traceback
        traceback.print_exc()
        logging.basicConfig(level=default_level)


def get_main_app_logger(module_name=None):
    if module_name:
        return logging.getLogger(f"main_app.{module_name}")
    return logging.getLogger("main_app")
