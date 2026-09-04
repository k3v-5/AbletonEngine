# tests/run_all_tests.py
import unittest
import sys
import os

# Add site-packages to path if not present
pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

def run():
    print("=" * 70)
    print("  PRODUCTION INTELLIGENCE ENGINE (PIE) - FASE 1, 2 & 2.5 TEST SUITE")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.dirname(__file__), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print(f"  TESTS RUN: {result.testsRun}")
    print(f"  ERRORS:    {len(result.errors)}")
    print(f"  FAILURES:  {len(result.failures)}")
    print(f"  STATUS:    {'ALL PASSED [SUCCESS]' if result.wasSuccessful() else '[FAILED]'}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run())
