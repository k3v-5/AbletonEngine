import os
import configparser

DEV_DIR = r"F:\Dev"

results = []
for item in sorted(os.listdir(DEV_DIR)):
    item_path = os.path.join(DEV_DIR, item)
    if not (os.path.isdir(item_path) or os.path.islink(item_path)):
        continue
    
    git_config_path = os.path.join(item_path, ".git", "config")
    remotes = {}
    is_git = os.path.exists(os.path.join(item_path, ".git"))
    
    if os.path.exists(git_config_path):
        try:
            config = configparser.ConfigParser()
            config.read(git_config_path)
            for section in config.sections():
                if section.startswith('remote "'):
                    remote_name = section.split('"')[1]
                    url = config.get(section, 'url', fallback='')
                    remotes[remote_name] = url
        except Exception as e:
            remotes["error"] = str(e)
            
    results.append({
        "name": item,
        "is_git": is_git,
        "has_config": os.path.exists(git_config_path),
        "remotes": remotes
    })

print(f"{'PROJECT':<25} | {'IS_GIT':<8} | {'REMOTES'}")
print("-" * 80)
for r in results:
    rem_str = ", ".join([f"{k}: {v}" for k, v in r["remotes"].items()]) if r["remotes"] else "None"
    print(f"{r['name']:<25} | {str(r['is_git']):<8} | {rem_str}")
