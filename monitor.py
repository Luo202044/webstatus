import json
import time
import urllib.request
import urllib.error
import os
from datetime import datetime
from typing import Dict, List

# 优先从环境变量读取 UA（GitHub Actions 中由 Secret 提供）
# 本地测试时可以设置环境变量，或使用下面的默认值（仅用于测试，不会用在生产）
DEFAULT_UA = "CustomHealthBot/1.2 (Compatible; LocalTest; Secured-UA/local_test_token)"
CUSTOM_UA = os.environ.get("MONITOR_UA", DEFAULT_UA)

def check_status(domain: str) -> Dict:
    """发送 GET 请求到 https://domain/ ，使用特殊 UA 绕过 CF 质询"""
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            status_code = resp.getcode()
            # 读取少量数据后关闭连接，减少流量
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
    # 读取需要监控的子域列表
    with open("config.json", "r") as f:
        config = json.load(f)
    domains: List[str] = config["domains"]

    results = [check_status(d) for d in domains]

    # 确保 data 目录存在
    os.makedirs("data", exist_ok=True)

    output = {
        "last_full_check": datetime.utcnow().isoformat() + "Z",
        "results": results
    }
    with open("data/status.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
