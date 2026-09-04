# tests/run_all_tests.py
import sys
import os

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)


def run():
    print("=" * 70)
    print("  PRODUCTION INTELLIGENCE ENGINE (PIE) - COMPLETE TEST SUITE")
    print("  PHASES 1-6 + HITO 1 (GATES 1, 2, 3, 4)")
    print("=" * 70)

    try:
        import pytest
        exit_code = pytest.main([os.path.dirname(__file__), "-v"])
        return exit_code
    except ImportError:
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover(os.path.dirname(__file__), pattern="test_*.py")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run())
