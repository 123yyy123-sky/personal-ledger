# -*- coding: utf-8 -*-
"""空仓库备用通道: Contents API 首文件 + Git Data API 完整提交"""
import base64, json, subprocess, urllib.request, os, sys

REPO_DIR = r"F:\Ai\github\personal-ledger"
OWNER, REPO = "123yyy123-sky", "personal-ledger"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

p = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                   capture_output=True, text=True)
T = [l.split("=",1)[1] for l in p.stdout.splitlines() if l.startswith("password=")][0]
HDR = {"Authorization": f"token {T}", "Accept": "application/vnd.github+json",
       "Content-Type": "application/json"}

def api(method, url, payload=None, ok=(200,201)):
    req = urllib.request.Request(f"{API}/{url}", method=method,
                                 data=json.dumps(payload).encode() if payload is not None else None,
                                 headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"HTTP {e.code}: {body}")
        if e.code not in ok:
            sys.exit(1)
        return {}

files = sorted(f for f in os.listdir(REPO_DIR) if f != ".git" and os.path.isfile(os.path.join(REPO_DIR, f)))

# 1. Contents API 落首文件 (空仓库唯一可用入口)
first = files[0]
data = base64.b64encode(open(os.path.join(REPO_DIR, first), "rb").read()).decode()
r = api("PUT", f"contents/{urllib.parse.quote(first)}",
        {"message": "init", "content": data}, ok=(200,201,422))
print(f"contents init: {first}")

# 2. Git Data API: 一次性树 + 提交 + 强制覆盖 main
items = []
for name in files:
    content = base64.b64encode(open(os.path.join(REPO_DIR, name), "rb").read()).decode()
    blob = api("POST", "git/blobs", {"content": content, "encoding": "base64"})
    items.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
print(f"blobs: {len(items)}")

tree = api("POST", "git/trees", {"tree": items})
ref = api("GET", "git/ref/heads/main")
parent = ref["object"]["sha"]
commit = api("POST", "git/commits", {
    "message": "个人记账本 v1.1：单文件复式记账 HTML 应用（PWA）",
    "tree": tree["sha"], "parents": [parent],
    "author": {"name": "123yyy123-sky", "email": "123yyy123-sky@users.noreply.github.com"},
    "committer": {"name": "123yyy123-sky", "email": "123yyy123-sky@users.noreply.github.com"},
})
req = urllib.request.Request(f"{API}/git/refs/heads/main", method="PATCH",
                             data=json.dumps({"sha": commit["sha"]}).encode(), headers=HDR)
with urllib.request.urlopen(req, timeout=30) as resp:
    print("main ->", json.loads(resp.read().decode())["object"]["sha"][:10])
print("DONE")
