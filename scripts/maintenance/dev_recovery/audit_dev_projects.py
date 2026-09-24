"""
Auditor for all projects in F:\\Dev
Checks git status, missing tracked files, diffs, remotes, and general project health.
"""

import os
import sys
import subprocess
import json

DEV_DIR = r"F:\Dev"

def run_git(cwd: str, args: list) -> tuple:
    try:
        res = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True, timeout=15)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def audit_project(folder_name: str) -> dict:
    full_path = os.path.join(DEV_DIR, folder_name)
    report = {
        "name": folder_name,
        "path": full_path,
        "is_symlink": os.path.islink(full_path),
        "is_git": False,
        "git_status": {},
        "missing_files": [],
        "modified_files": [],
        "untracked_count": 0,
        "remotes": [],
        "file_count": 0,
        "dir_count": 0,
        "zero_byte_files": [],
        "notes": []
    }

    if not os.path.isdir(full_path):
        report["notes"].append("Not a directory")
        return report

    git_dir = os.path.join(full_path, ".git")
    if os.path.exists(git_dir):
        report["is_git"] = True
        
        # 1. Remotes
        rc, out, _ = run_git(full_path, ["remote", "-v"])
        if rc == 0 and out:
            report["remotes"] = list(set([line.split()[1] for line in out.splitlines() if line]))

        # 2. Latest Commit
        rc, out, _ = run_git(full_path, ["log", "-1", "--oneline"])
        report["last_commit"] = out if rc == 0 else "NO_COMMITS_OR_CORRUPT"

        # 3. Status - Missing tracked files
        rc, out, _ = run_git(full_path, ["status", "--porcelain"])
        if rc == 0:
            for line in out.splitlines():
                if not line.strip():
                    continue
                code = line[:2]
                fname = line[3:].strip()
                if "D" in code:
                    report["missing_files"].append(fname)
                elif "M" in code:
                    report["modified_files"].append(fname)
                elif "??" in code:
                    report["untracked_count"] += 1
        else:
            report["notes"].append(f"Git status error: {_}")

    # General file inspection
    total_files = 0
    total_dirs = 0
    zero_bytes = []
    manifests = []
    
    for root, dirs, files in os.walk(full_path):
        # Skip .git internals from file count
        if ".git" in dirs:
            dirs.remove(".git")
        if "node_modules" in dirs:
            dirs.remove("node_modules")
            report["has_node_modules"] = True
        if ".venv" in dirs or "venv" in dirs:
            dirs[:] = [d for d in dirs if d not in (".venv", "venv")]
            report["has_venv"] = True

        total_dirs += len(dirs)
        total_files += len(files)
        
        for f in files:
            fpath = os.path.join(root, f)
            if f in ("package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "build.gradle", "pom.xml", "CMakeLists.txt"):
                manifests.append(os.path.relpath(fpath, full_path))
            try:
                if os.path.getsize(fpath) == 0 and not f.startswith("."):
                    zero_bytes.append(os.path.relpath(fpath, full_path))
            except Exception:
                pass

    report["file_count"] = total_files
    report["dir_count"] = total_dirs
    report["zero_byte_files"] = zero_bytes[:20]  # sample first 20
    report["manifests"] = manifests

    return report

def main():
    items = sorted(os.listdir(DEV_DIR))
    all_reports = []
    
    for item in items:
        p = os.path.join(DEV_DIR, item)
        if os.path.isdir(p) or os.path.islink(p):
            rep = audit_project(item)
            all_reports.append(rep)

    out_file = r"F:\Dev\audit_dev_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)
    
    print(f"Audited {len(all_reports)} items in {DEV_DIR}. Report saved to {out_file}")

if __name__ == "__main__":
    main()
