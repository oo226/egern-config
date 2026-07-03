import os
import ssl
import urllib.request

RULES = [
    "Reject", "ChinaDomain", "Lan", "Direct",
    "WeChat", "Bilibili", "AppleCN", "ChinaIP", "ChinaASN",
    "AI", "Telegram", "Twitter", "TikTok",
    "YouTube", "Netflix", "Disney", "Spotify", "Emby",
    "Google", "Github", "Microsoft", "AppleServers",
    "Game", "ProxyGFW", "Proxy",
]
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Rules")
SKK_DIR = os.path.join(BASE_DIR, "skk")
os.makedirs(SKK_DIR, exist_ok=True)
CTX = ssl.create_default_context()

MIRRORS = [
    "https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules/{name}.yaml",
    "https://ghproxy.net/https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules/{name}.yaml",
    "https://mirror.ghproxy.com/https://raw.githubusercontent.com/Repcz/Tool/X/Egern/Rules/{name}.yaml",
]


def fetch(url: str, out: str) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=CTX, timeout=90) as resp:
        data = resp.read()
    with open(out, "wb") as f:
        f.write(data)
    return len(data)


def main() -> None:
    ok = fail = 0
    for name in RULES:
        out = os.path.join(BASE_DIR, f"{name}.yaml")
        done = False
        for tpl in MIRRORS:
            url = tpl.format(name=name)
            try:
                size = fetch(url, out)
                host = url.split("/")[2]
                print(f"OK {name}.yaml ({size} bytes) via {host}")
                ok += 1
                done = True
                break
            except Exception:
                continue
        if not done:
            print(f"FAIL {name}.yaml")
            fail += 1

    skk_urls = [
        "https://ruleset.skk.moe/List/domainset/reject.conf",
        "https://ghproxy.net/https://ruleset.skk.moe/List/domainset/reject.conf",
    ]
    for url in skk_urls:
        try:
            size = fetch(url, os.path.join(SKK_DIR, "reject.conf"))
            print(f"OK skk/reject.conf ({size} bytes)")
            break
        except Exception as exc:
            print(f"skk fail {url}: {exc}")

    print(f"summary ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
