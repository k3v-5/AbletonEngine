import os
import subprocess

repos = [
    'patrones-diseno', 'Portfolio', 'Gastos', 'CitasApp', 
    'AsistenteCelular', 'fl-studio-mcp-full-song', 
    'AdobeEngineSuit', 'after-effects-mcp', 
    'MAI/MAI', 'CO/career-ops', 'YT/pear-desktop', 'AbletonEngine'
]

total_restored = 0

for r in repos:
    p_path = os.path.join(r"F:\Dev", r.replace('/', os.sep))
    res = subprocess.run(['git', 'status', '--porcelain'], cwd=p_path, capture_output=True, text=True)
    to_restore = []
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
                    is_null = (set(fp.read(min(sz, 512))) == {0})
                if is_null:
                    to_restore.append(frel)
            except Exception:
                pass
        elif 'D' in code:
            to_restore.append(frel)

    for frel in to_restore:
        fpath = os.path.join(p_path, frel)
        # remove corrupted file first so git can write freely
        if os.path.exists(fpath):
            try:
                os.remove(fpath)
            except Exception:
                pass
        rc = subprocess.run(['git', 'checkout', '--', frel], cwd=p_path, capture_output=True, text=True)
        if rc.returncode == 0:
            print(f"Cleanly restored: {r} -> {frel}")
            total_restored += 1
        else:
            print(f"Error restoring {r} -> {frel}: {rc.stderr.strip()}")

print(f"\nTotal files cleanly restored: {total_restored}")
