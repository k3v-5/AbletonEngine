import json

with open(r'F:\Dev\audit_dev_report.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f'Total projects audited: {len(data)}')
print('=' * 80)
for p in data:
    name = p['name']
    is_git = p['is_git']
    fc = p['file_count']
    missing = len(p.get('missing_files', []))
    mod = len(p.get('modified_files', []))
    untracked = p.get('untracked_count', 0)
    manifests = ', '.join(p.get('manifests', []))
    last_c = p.get('last_commit', 'N/A')
    
    status_flags = []
    if is_git:
        status_flags.append('GIT')
        if missing > 0:
            status_flags.append(f'MISSING_FILES: {missing}')
        if mod > 0:
            status_flags.append(f'MODIFIED: {mod}')
        if untracked > 0:
            status_flags.append(f'UNTRACKED: {untracked}')
        if missing == 0 and mod == 0:
            status_flags.append('CLEAN')
    else:
        status_flags.append('NO-GIT')
        
    flags_str = ' | '.join(status_flags)
    print(f'[{name}] ({fc} files) -> {flags_str}')
    if is_git:
        print(f'   Commit: {last_c}')
        if p.get('remotes'):
            print(f'   Remotes: {p["remotes"]}')
        if missing > 0:
            print(f'   Missing sample (total {missing}): {p["missing_files"][:5]}')
        if mod > 0:
            print(f'   Modified sample (total {mod}): {p["modified_files"][:5]}')
    if manifests:
        print(f'   Manifests: {manifests}')
    if p.get('notes'):
        print(f'   Notes: {p["notes"]}')
    print('-' * 80)
