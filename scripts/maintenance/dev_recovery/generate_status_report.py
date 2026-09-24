"""
Generates a complete, granular audit of every project in F:\Dev:
- Counts valid files vs null-corrupted files
- Breaks down by extension (.ts, .js, .py, .rs, .json, .md, etc.)
- Lists key intact files and key corrupted files
- Inspects git commit & branch info
"""

import os
import sys
import json

DEV_DIR = r"F:\Dev"
projects = sorted([p for p in os.listdir(DEV_DIR) if os.path.isdir(os.path.join(DEV_DIR, p))])

report = {}

for p in projects:
    p_path = os.path.join(DEV_DIR, p)
    
    valid_files = []
    corrupt_null_files = []
    empty_zero_files = []
    
    ext_breakdown_valid = {}
    ext_breakdown_corrupt = {}

    for root, dirs, files in os.walk(p_path):
        # Exclude build caches and node_modules from detailed source audit, but count them if present
        is_cache = any(ign in root for ign in ['.git', 'node_modules', 'target', '.venv', 'env', '.angular', 'build', '.next', '__pycache__'])
        if is_cache:
            continue
            
        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, p_path)
            ext = os.path.splitext(f)[1].lower() or '[no_ext]'
            
            try:
                sz = os.path.getsize(fpath)
                if sz == 0:
                    empty_zero_files.append(rel)
                    continue
                
                with open(fpath, 'rb') as fp:
                    header = fp.read(min(sz, 512))
                    if set(header) == {0}:
                        corrupt_null_files.append((rel, sz, ext))
                        ext_breakdown_corrupt[ext] = ext_breakdown_corrupt.get(ext, 0) + 1
                    else:
                        valid_files.append((rel, sz, ext))
                        ext_breakdown_valid[ext] = ext_breakdown_valid.get(ext, 0) + 1
            except Exception as e:
                corrupt_null_files.append((rel, 0, f"ERR:{e}"))

    # Git metadata inspection
    git_dir = os.path.join(p_path, '.git')
    git_info = {'is_git': os.path.exists(git_dir), 'remotes': [], 'branch': None, 'last_commit': None}
    if os.path.exists(git_dir):
        # config
        cfg = os.path.join(git_dir, 'config')
        if os.path.exists(cfg):
            try:
                with open(cfg, 'r', errors='ignore') as cf:
                    for line in cf:
                        if 'url =' in line:
                            git_info['remotes'].append(line.split('=', 1)[1].strip())
            except Exception:
                pass
        # head
        head_f = os.path.join(git_dir, 'HEAD')
        if os.path.exists(head_f):
            try:
                with open(head_f, 'r', errors='ignore') as hf:
                    git_info['head_ref'] = hf.read().strip()
            except Exception:
                pass

    report[p] = {
        'total_source_files': len(valid_files) + len(corrupt_null_files) + len(empty_zero_files),
        'valid_count': len(valid_files),
        'corrupt_count': len(corrupt_null_files),
        'empty_zero_count': len(empty_zero_files),
        'ext_valid': ext_breakdown_valid,
        'ext_corrupt': ext_breakdown_corrupt,
        'sample_valid': [f[0] for f in valid_files[:10]],
        'sample_corrupt': [f[0] for f in corrupt_null_files[:10]],
        'git': git_info
    }

with open(r"F:\Dev\project_recovery_status.json", 'w', encoding='utf-8') as out:
    json.dump(report, out, indent=2)

print("Status report generated successfully.")
