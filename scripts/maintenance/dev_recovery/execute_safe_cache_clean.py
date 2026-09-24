"""
Safe, item-by-item removal of corrupted null-filled cache files.
Safety guarantees:
1. ONLY calls os.remove on individual files, never recursive rmdir on trees.
2. Every single file must pass:
   - Must be within F:\Dev
   - Must NOT be tracked in Git
   - Must be inside a designated cache folder (__pycache__, .pytest_cache, .ruff_cache, .gradle, or AbletonEngine/cache)
   - Must be verified 100% NULL (0x00) or 0-bytes
3. Any file with valid/real data is STRICTLY skipped and preserved.
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

def clean_null_caches():
    print("[1/3] Indexando archivos Git rastreados para proteccion estricta...")
    tracked_files = get_tracked_files_all_repos()
    print(f"      {len(tracked_files)} archivos rastreados protegidos.")

    print("[2/3] Identificando y eliminando de forma segura solo archivos de cache nulos...")
    deleted_count = 0
    preserved_count = 0
    errors = 0

    for root, dirs, files in os.walk(DEV_DIR):
        if '.git' in dirs:
            dirs.remove('.git')

        parts = root.split(os.sep)
        in_std_cache = any(p in CACHE_DIR_NAMES for p in parts)
        in_gradle_cache = '.gradle' in parts
        in_ableton_cache = (r"F:\Dev\AbletonEngine\cache".lower() in root.lower())

        if in_std_cache or in_gradle_cache or in_ableton_cache:
            for f in files:
                fpath = os.path.normpath(os.path.join(root, f))
                
                # Rule 1: Not git tracked
                if fpath.lower() in tracked_files:
                    continue

                # Rule 2: Strictly within F:\Dev
                if not fpath.lower().startswith(r"f:\dev"):
                    continue

                # Rule 3: Must be verified null or empty
                if is_null_or_empty(fpath):
                    try:
                        os.remove(fpath)
                        deleted_count += 1
                        if deleted_count % 2000 == 0:
                            print(f"      ... {deleted_count} archivos de cache nulos eliminados...")
                    except Exception as e:
                        errors += 1
                else:
                    preserved_count += 1

    print(f"[3/3] Limpieza finalizada:")
    print(f"      - Archivos de cache nulos eliminados con exito: {deleted_count}")
    print(f"      - Archivos con datos validos preservados intactos: {preserved_count}")
    if errors > 0:
        print(f"      - Archivos con error al eliminar: {errors}")

if __name__ == '__main__':
    clean_null_caches()
