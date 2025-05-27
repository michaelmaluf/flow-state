#!/usr/bin/env python3
import os
import subprocess

import yaml


def build_app():
    # Clean previous builds
    if os.path.exists('dist'):
        import shutil
        shutil.rmtree('dist')
    if os.path.exists('build'):
        import shutil
        shutil.rmtree('build')

    db_url = os.getenv('FLOWSTATE_DATABASE_URL')
    api_key = os.getenv('FLOWSTATE_AI_API_KEY')

    if not db_url or not api_key:
        print("❌ Set FLOWSTATE_DATABASE_URL and FLOWSTATE_AI_API_KEY before building")
        return

    # Write actual values to config
    config = {
        'database_url': db_url,
        'ai_api_key': api_key
    }

    with open('resources/config/config.yaml', 'w') as f:
        yaml.dump(config, f)

    # Build command
    cmd = [
        'pyinstaller',
        '--onedir',
        '--optimize', '2',
        '--exclude-module', 'numpy',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'contourpy',
        '--exclude-module', 'fonttools',
        '--exclude-module', 'cycler',
        '--exclude-module', 'kiwisolver',
        '--windowed',
        '--icon=icon.icns',
        '--add-data', 'resources:resources',
        '--name', 'FlowState',
        'main.py'
    ]

    subprocess.run(cmd)
    print("Build complete! Check the dist/ folder.")


if __name__ == "__main__":
    build_app()