# log.py
import logging
import logging.config
import logging.handlers
import os

import yaml


class DebugFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG


def setup_logging(default_path='log.yaml', default_level=logging.INFO):
    """Setup logging configuration"""
    try:
        root_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(root_dir, "logs")
        config_path = os.path.join(root_dir, default_path)

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

            # Register the DebugFilter directly in code
            logging.config.dictConfig(config)

            # Add the filter manually after config is loaded
            debug_handler = logging.getLogger('main_app').handlers[2]  # Assuming debug_file is the third handler
            debug_handler.addFilter(DebugFilter())

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