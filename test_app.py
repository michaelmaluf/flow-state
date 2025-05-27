import os
import subprocess
import sys
from pathlib import Path


class PyInstallerTester:
    def __init__(self):
        self.results = {}
        self.exe_path = None

    def log_result(self, test_name, success, message=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"    {message}")

        self.results[test_name] = {
            'success': success,
            'message': message
        }

    def test_imports(self):
        """Test that all imports work"""
        try:
            import app
            from app.utils import resolve_path
            self.log_result("Module Imports", True, "All modules importable")
            return True
        except ImportError as e:
            self.log_result("Module Imports", False, f"Import error: {e}")
            return False

    def test_resources(self):
        """Test resource access in development"""
        try:
            from app.utils.resolve_path import get_config_path, get_script_path, get_image_path

            path = get_config_path('log.yaml')
            if not os.path.exists(path):
                raise FileNotFoundError(f"Resource not found: {path}")

            path = get_script_path('get_current_application.sh')
            if not os.path.exists(path):
                raise FileNotFoundError(f"Resource not found: {path}")

            path = get_image_path('icon.jpg')
            if not os.path.exists(path):
                raise FileNotFoundError(f"Resource not found: {path}")

            self.log_result("Resource Access", True, f"All resources found")
            return True

        except Exception as e:
            self.log_result("Resource Access", False, str(e))
            return False

    def test_logging(self):
        """Test logging setup"""
        try:
            from app.utils.log import setup_logging, get_main_app_logger, get_logs_directory
            import logging

            # Setup logging
            setup_logging()
            logger = get_main_app_logger()

            # Test that we can actually log
            logger.info("Test log message")

            # Get logs directory and verify
            logs_dir = get_logs_directory()
            from pathlib import Path
            logs_path = Path(logs_dir)

            if logs_path.exists():
                log_files = list(logs_path.glob('*.log'))
                self.log_result('Logging Setup', True,
                                f'Logs dir: {logs_dir}, {len(log_files)} log files')
            else:
                self.log_result('Logging Setup', True, 'Logging works (dir not found)')

            return True

        except Exception as e:
            self.log_result("Logging Setup", False, str(e))
            return False

    def test_build(self):
        """Test PyInstaller build"""
        try:
            result = subprocess.run([sys.executable, 'build_app.py'],
                                    capture_output=True, text=True, timeout=600)

            if result.returncode != 0:
                self.log_result("Build Process", False, result.stderr)
                return False

            dist_dir = Path('dist')

            # CASE 1: First check for onedir (folder structure)
            app_folders = [f for f in dist_dir.glob('*') if f.is_dir()]
            if app_folders:
                # onedir - look for executable inside folder
                app_folder = app_folders[0]
                exe_files = [f for f in app_folder.glob('*')
                             if f.is_file() and os.access(f, os.X_OK) and not f.name.startswith('_')]
                if exe_files:
                    self.exe_path = exe_files[0]
                    # Calculate folder size for onedir
                    folder_size = sum(f.stat().st_size for f in app_folder.rglob('*') if f.is_file())
                    folder_size_mb = folder_size / (1024 * 1024)
                    self.log_result("Build Process", True,
                                    f"Executable: {self.exe_path} (folder: {folder_size_mb:.1f} MB)")
                    return True

            # CASE 2: Fall back to onefile check
            exe_files = [f for f in dist_dir.glob('*')
                         if f.is_file() and os.access(f, os.X_OK)]
            if exe_files:
                self.exe_path = exe_files[0]
                file_size = self.exe_path.stat().st_size / (1024 * 1024)
                self.log_result("Build Process", True,
                                f"Executable: {self.exe_path} ({file_size:.1f} MB)")
                return True

            self.log_result("Build Process", False, "No executable found in dist/")
            return False

        except subprocess.TimeoutExpired:
            self.log_result("Build Process", False, "Build timed out (10 minutes)")
            return False
        except Exception as e:
            self.log_result("Build Process", False, str(e))
            return False

    def test_executable_basic(self):
        """Test basic executable functionality"""
        if not self.exe_path:
            self.log_result("Executable Basic", False, "No executable to test")
            return False

        if os.access(self.exe_path, os.X_OK):
            if self.exe_path.is_file():
                self.log_result("Executable Basic", True, "Executable exists and is executable")
                return True
            else:
                self.log_result("Executable Basic", False, "Path is not a file")
                return False
        else:
            self.log_result("Executable Basic", False, "Executable not executable")
            return False

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting Comprehensive PyInstaller Tests\n")

        tests = [
            self.test_imports,
            self.test_resources,
            self.test_logging,
            self.test_build,
            self.test_executable_basic,
        ]

        for test in tests:
            test()
            print()  # Empty line between tests

        # Summary
        passed = sum(1 for result in self.results.values() if result['success'])
        total = len(self.results)

        print(f"📊 Summary: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 All tests passed! Your PyInstaller setup is ready.")
        else:
            print("⚠️  Some tests failed. Review the output above.")

        return passed == total


if __name__ == "__main__":
    tester = PyInstallerTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)