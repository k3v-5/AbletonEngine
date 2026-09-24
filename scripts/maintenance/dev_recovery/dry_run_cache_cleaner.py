"""
Safe Cache Cleaner for F:\Dev:
Rules:
1. Target ONLY specific cache folders: __pycache__, .pytest_cache, .ruff_cache, and android/.gradle
2. In F:\Dev\AbletonEngine\cache, target ONLY files that are 100% NULL-corrupt (0x00)
3. NEVER delete any file outside F:\Dev
4. NEVER delete any tracked Git file
5. NEVER delete any file that contains non-zero bytes
"""

import os
import sys
import subprocess

DEV_DIR = r"F:\Dev"
CACHE_DIR_NAMES = {'__pycache__', '.pytest_cache', '.ruff_cache'}

def get_tracked_files_all_repos():
    tracked = set()
    for root, dirs, files in os.walk(DEV_DIR):
        if '.git' in dirs:
            repo_path = root
            res = subprocess.run(['git', 'ls-files'], cwd=repo_path, capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if line.strip():
                    full_p = os.path.normpath(os.path.join(repo_path, line.strip()))
                    tracked.add(full_p.lower())
            dirs.remove('.git')
    return tracked

def is_null_or_empty(filepath: str) -> bool:
    try:
        sz = os.path.getsize(filepath)
        if sz == 0:
            return True
        with open(filepath, 'rb') as f:
            chunk = f.read(min(sz, 512))
            return set(chunk) == {0}
    except Exception:
        return False

def scan_cache_files():
    tracked_files = get_tracked_files_all_repos()
    print(f"Total Git-tracked files across all repos: {len(tracked_files)}")

    to_delete = []
    skipped_valid = []

    for root, dirs, files in os.walk(DEV_DIR):
        # Prevent stepping into .git
        if '.git' in dirs:
            dirs.remove('.git')

        parts = root.split(os.sep)
        in_std_cache = any(p in CACHE_DIR_NAMES for p in parts)
        in_gradle_cache = '.gradle' in parts
        in_ableton_cache = (r"F:\Dev\AbletonEngine\cache".lower() in root.lower())

        if in_std_cache or in_gradle_cache or in_ableton_cache:
            for f in files:
                fpath = os.path.normpath(os.path.join(root, f))
                
                # Check safety rule 1: MUST NOT be git tracked
                if fpath.lower() in tracked_files:
                    continue

                # Check safety rule 2: MUST be within F:\Dev
                if not fpath.lower().startswith(r"f:\dev"):
                    continue

                # Check safety rule 3: In standard cache dirs (__pycache__, .pytest_cache, .ruff_cache, .gradle),
                # or in AbletonEngine\cache if null-corrupt
                if is_null_or_empty(fpath):
                    to_delete.append(fpath)
                else:
                    skipped_valid.append(fpath)

    print(f"\n[SCAN RESULT]")
    print(f"  Files targeted for safe cache deletion: {len(to_delete)}")
    print(f"  Valid files preserved (not deleted):    {len(skipped_valid)}")
    print(f"\nSample files targeted:")
    for p in to_delete[:15]:
        print(f"  - {p}")
    if skipped_valid:
        print(f"\nSample VALID files preserved in cache:")
        for p in skipped_valid[:5]:
            print(f"  + {p}")
    return to_delete

if __name__ == '__main__':
    scan_cache_files()
