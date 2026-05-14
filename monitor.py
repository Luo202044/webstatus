import json
import time
import urllib.request
import urllib.error
import os
from datetime import datetime
from typing import Dict, List, Union

CUSTOM_UA = "CustomHealthBot/1.2 (Compatible; GHA-Monitor; +https://yourdomain.com/bot) Secured-UA/7d131d2009450739"

# ────────── 禁止自动跟随重定向 ──────────
class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

    http_error_301 = redirect_request
    http_error_302 = redirect_request
    http_error_303 = redirect_request
    http_error_307 = redirect_request
# ─────────────────────────────────────────

def check_status(domain: str) -> Dict:
    url = f"https://{domain}/"
    start = time.time()
    status_code = None
    ok = False
    error_msg = None

    try:
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', CUSTOM_UA)
        req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        req.add_header('Accept-Language', 'zh-CN,zh;q=0.9,en;q=0.8')

        opener = urllib.request.build_opener(NoRedirectHandler)
        with opener.open(req, timeout=15) as resp:
            status_code = resp.getcode()
            _ = resp.read(1024)
            ok = 200 <= status_code < 400

    except urllib.error.HTTPError as e:
        status_code = e.code
        ok = False
        error_msg = str(e)
    except Exception as e:
        status_code = None
        ok = False
        error_msg = str(e)

    elapsed = round((time.time() - start) * 1000)

    return {
        "domain": domain,
        "status_code": status_code,
        "ok": ok,
        "response_time_ms": elapsed,
        "checked_at": datetime.utcnow().isoformat() + "Z",
        "error": error_msg if error_msg else None
    }

def main():
    with open("config.json", "r", encoding="utf-8") as f:
        raw_config = json.load(f)

    # ───── 关键修正：兼容你的 config.json 格式 ─────
    # 你的 config.json 是 {"domains": [...]} 结构
    if isinstance(raw_config, dict) and "domains" in raw_config:
        raw_list = raw_config["domains"]
    elif isinstance(raw_config, list):
        raw_list = raw_config   # 兼容旧的数组格式
    else:
        raise ValueError("config.json 格式错误：需要 {'domains': [...]} 或 [...] 数组")

    # 统一转换为对象数组（确保每个条目都有 domain 和 name）
    config: List[Dict[str, str]] = []
    for item in raw_list:
        if isinstance(item, str):
            config.append({"domain": item, "name": item})
        elif isinstance(item, dict) and "domain" in item:
            # 确保 name 存在，不存在则用 domain 作为名称
            config.append({
                "domain": item["domain"],
                "name": item.get("name", item["domain"])
            })
        else:
            print(f"⚠️ 跳过无效配置项: {item}")

    domains = [item["domain"] for item in config]
    results = [check_status(domain) for domain in domains]

    report = {
        "config": config,
        "results": results,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    os.makedirs("data", exist_ok=True)
    with open("data/status.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
