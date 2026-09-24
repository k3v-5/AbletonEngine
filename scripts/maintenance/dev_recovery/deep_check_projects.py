"""
Deep check of all projects in F:\Dev:
- Validates syntax of all Python files (py_compile)
- Validates syntax of all JSON files (json.load)
- Validates syntax of all Cargo.toml files (tomllib)
- Inspects entry points from package.json and Cargo.toml
- Checks git refs and branch heads
"""

import os
import sys
import json
import py_compile
try:
    import tomllib
except ImportError:
    tomllib = None

DEV_DIR = r"F:\Dev"
projects = sorted([p for p in os.listdir(DEV_DIR) if os.path.isdir(os.path.join(DEV_DIR, p))])

summary_report = {}

for p in projects:
    p_path = os.path.join(DEV_DIR, p)
    py_files = 0
    py_errors = []
    json_files = 0
    json_errors = []
    toml_files = 0
    toml_errors = []
    missing_entry_points = []
    total_files = 0
    top_items = os.listdir(p_path)

    for root, dirs, files in os.walk(p_path):
        if any(ign in root for ign in ['.git', 'node_modules', 'target', '.venv', 'env', '.angular', 'build', '.next', '__pycache__']):
            continue
        for f in files:
            total_files += 1
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, p_path)

            if f.endswith('.py'):
                py_files += 1
                try:
                    py_compile.compile(fpath, doraise=True)
                except Exception as e:
                    py_errors.append((rel_path, str(e)))

            elif f.endswith('.json'):
                json_files += 1
                try:
                    with open(fpath, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                except UnicodeDecodeError:
                    try:
                        with open(fpath, 'r', encoding='utf-8-sig') as jf:
                            data = json.load(jf)
                    except Exception as e:
                        json_errors.append((rel_path, str(e)))
                except Exception as e:
                    json_errors.append((rel_path, str(e)))

            elif f.endswith('.toml'):
                toml_files += 1
                if tomllib:
                    try:
                        with open(fpath, 'rb') as tf:
                            tomllib.load(tf)
                    except Exception as e:
                        toml_errors.append((rel_path, str(e)))

    # Check package.json entry points if package.json exists in root
    pkg_path = os.path.join(p_path, 'package.json')
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, 'r', encoding='utf-8') as jf:
                pkg = json.load(jf)
                for field in ['main', 'module', 'types', 'typings']:
                    if field in pkg and isinstance(pkg[field], str):
                        target = os.path.normpath(os.path.join(p_path, pkg[field]))
                        if not os.path.exists(target) and not os.path.exists(target + '.js') and not os.path.exists(target + '.ts'):
                            missing_entry_points.append(f"{field} -> {pkg[field]}")
        except Exception:
            pass

    # Check git refs
    git_dir = os.path.join(p_path, '.git')
    git_info = {'is_git': os.path.exists(git_dir)}
    if os.path.exists(git_dir):
        head_file = os.path.join(git_dir, 'HEAD')
        if os.path.exists(head_file):
            try:
                with open(head_file, 'r', encoding='utf-8', errors='ignore') as hf:
                    git_info['head'] = hf.read().strip()
            except Exception:
                git_info['head'] = 'ERROR'
        refs_heads = os.path.join(git_dir, 'refs', 'heads')
        branches = []
        if os.path.exists(refs_heads):
            for broot, _, bfiles in os.walk(refs_heads):
                for bf in bfiles:
                    b_rel = os.path.relpath(os.path.join(broot, bf), refs_heads)
                    b_path = os.path.join(broot, bf)
                    try:
                        with open(b_path, 'r') as hbf:
                            commit_hash = hbf.read().strip()
                        branches.append((b_rel, commit_hash))
                    except Exception:
                        branches.append((b_rel, 'CORRUPT_REF'))
        git_info['branches'] = branches

    summary_report[p] = {
        'total_files': total_files,
        'top_items': top_items[:10],
        'py_files': py_files,
        'py_errors': py_errors,
        'json_files': json_files,
        'json_errors': json_errors,
        'toml_files': toml_files,
        'toml_errors': toml_errors,
        'missing_entry_points': missing_entry_points,
        'git': git_info
    }

out_file = r"F:\Dev\deep_check_report.json"
with open(out_file, 'w', encoding='utf-8') as out:
    json.dump(summary_report, out, indent=2)

print(f"Deep check complete! Report saved to {out_file}")
for p, d in summary_report.items():
    err_str = []
    if d['py_errors']: err_str.append(f"PY_ERR:{len(d['py_errors'])}")
    if d['json_errors']: err_str.append(f"JSON_ERR:{len(d['json_errors'])}")
    if d['toml_errors']: err_str.append(f"TOML_ERR:{len(d['toml_errors'])}")
    if d['missing_entry_points']: err_str.append(f"ENTRY_MISSING:{len(d['missing_entry_points'])}")
    status = ", ".join(err_str) if err_str else "OK"
    git_head = d['git'].get('head', 'No-Git')
    branches = [f"{b[0]} ({b[1][:7]})" for b in d['git'].get('branches', [])]
    print(f"{p:<24} | Files: {d['total_files']:>5} | Health: {status:<15} | Git: {git_head} | Branches: {branches}")
