import os
import subprocess

repos = [
    'Gastos', 'CitasApp', 'AdobeEngineSuit', 'after-effects-mcp', 
    'CO/career-ops', 'YT/pear-desktop', 'AbletonEngine'
]

for r in repos:
    p_path = os.path.join(r"F:\Dev", r.replace('/', os.sep))
    res = subprocess.run(['git', 'status', '--porcelain'], cwd=p_path, capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if not line.strip(): 
            continue
        code = line[:2]
        frel = line[3:].strip().strip('"')
        fpath = os.path.join(p_path, frel)
        if 'M' in code:
            try:
                sz = os.path.getsize(fpath)
                with open(fpath, 'rb') as fp:
                    if set(fp.read(min(sz, 512))) == {0}:
                        print(f"{r} -> Null-corrupt: {frel}")
            except Exception as e:
                pass
        elif 'D' in code:
            print(f"{r} -> Deleted: {frel}")
