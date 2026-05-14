import json
import time
import urllib.request
import urllib.error
import os
from datetime import datetime
from typing import Dict, List

# 自定义 User-Agent（可根据需要修改）
CUSTOM_UA = "CustomHealthBot/1.2 (Compatible; GHA-Monitor; +https://yourdomain.com/bot) Secured-UA/7d131d2009450739"

# ───────────────── 关键修改：阻止自动跟随重定向 ─────────────────
class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """自定义处理器，对于重定向响应，不自动跟随，直接返回原始响应"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # 返回 None 即可阻止跟随

    # 明确注册常见的重定向状态码
    http_error_301 = redirect_request
    http_error_302 = redirect_request
    http_error_303 = redirect_request
    http_error_307 = redirect_request
# ───────────────────────────────────────────────────────────────

def check_status(domain: str) -> Dict:
    """检查单个域名的 HTTPS 状态"""
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

        # 使用自定义 opener（不会自动跟随重定向）
        opener = urllib.request.build_opener(NoRedirectHandler)
        with opener.open(req, timeout=15) as resp:
            status_code = resp.getcode()
            # 仍然只读取一小部分数据以释放连接
            _ = resp.read(1024)
            # 2xx/3xx 均视为正常（但此时3xx不会再被自动处理，会被直接返回）
            ok = 200 <= status_code < 400

    except urllib.error.HTTPError as e:
        # 4xx/5xx 错误会进入这里
        status_code = e.code
        ok = False
        error_msg = str(e)
    except Exception as e:
        # 网络错误、超时等
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
    # 读取配置
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # 提取域名列表（假设 config.json 结构为 [{"domain": "...", "name": "..."}, ...]）
    domains = [item["domain"] for item in config]

    results = []
    for domain in domains:
        result = check_status(domain)
        results.append(result)

    # 生成 status.json
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
