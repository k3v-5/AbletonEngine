import os
import subprocess

repos = [
    'patrones-diseno', 'Gastos', 'CitasApp', 'AsistenteCelular', 
    'fl-studio-mcp-full-song', 'AdobeEngineSuit', 'after-effects-mcp', 
    'MAI/MAI', 'CO/career-ops', 'YT/pear-desktop', 'AbletonEngine'
]

for r in repos:
    p_path = os.path.join(r"F:\Dev", r.replace('/', os.sep))
    res = subprocess.run(['git', 'status', '--porcelain'], cwd=p_path, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"{r}: git error -> {res.stderr.strip()[:100]}")
        continue
    
    null_modified = []
    real_modified = []
    untracked = []
    deleted = []

    for line in res.stdout.splitlines():
        if not line.strip(): 
            continue
        code = line[:2]
        frel = line[3:].strip().strip('"')
        fpath = os.path.join(p_path, frel)
        if '?' in code:
            untracked.append(frel)
        elif 'D' in code:
            deleted.append(frel)
        elif 'M' in code:
            try:
                sz = os.path.getsize(fpath)
                with open(fpath, 'rb') as fp:
                    hdr = fp.read(min(sz, 512))
                    if set(hdr) == {0}:
                        null_modified.append(frel)
                    else:
                        real_modified.append(frel)
            except Exception:
                null_modified.append(frel)
    
    print(f"=== {r} ===")
    print(f"  Deleted (missing): {len(deleted)}")
    print(f"  Null-modified (corrupt): {len(null_modified)}")
    print(f"  Real-modified (user edits): {len(real_modified)}")
    print(f"  Untracked (new files): {len(untracked)}")
    if real_modified:
        print(f"    Real modified samples: {real_modified[:5]}")
