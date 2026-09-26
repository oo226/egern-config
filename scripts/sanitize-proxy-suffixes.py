#!/usr/bin/env python3
"""Strip bare domain_suffix entries (no dot) from ProxyGFW / Proxy.

Egern DOMAIN-SUFFIX,sh matches every *.sh host — steals Cursor (api2.cursor.sh)
from the AI rule. Same for ai/io/jp/… country & generic TLDs.
Useful tokens (chrome/goog/aws…) are moved to domain_keyword_set.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# guize 分流在 Egern/Routing；sync 日更可能在 Routing/
CANDIDATE_DIRS = (
    ROOT / "Egern" / "Routing" / "Foreign",
    ROOT / "Routing" / "Foreign",
)

# Bare labels worth keeping as keyword (not as whole-TLD suffix)
KEEP_AS_KEYWORD = {
    "aws", "chrome", "community", "gle", "goog", "guru", "lol", "network",
    "party", "rocks", "cafe", "adult", "amazon", "bet", "sex", "xxx", "one",
    "new", "rip",
}

TARGETS = ("ProxyGFW.yaml", "Proxy.yaml")


def sanitize(path: Path) -> None:
    if not path.is_file():
        print(f"skip missing {path}")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    section: str | None = None
    keywords: list[str] = []
    removed: list[str] = []
    existing_kw: set[str] = set()

    # first pass: collect existing keywords
    cur = None
    for line in lines:
        s = line.strip()
        if s == "domain_keyword_set:":
            cur = "kw"
            continue
        if s.endswith(":") and not s.startswith("-"):
            cur = None
            continue
        if cur == "kw" and s.startswith("- "):
            existing_kw.add(s[2:].strip().lower())

    for line in lines:
        s = line.strip()
        if s.endswith(":") and not s.startswith("#") and not s.startswith("-"):
            section = s[:-1]
            out.append(line)
            continue
        if section == "domain_suffix_set" and s.startswith("- "):
            val = s[2:].strip()
            if "." not in val:
                removed.append(val)
                if val.lower() in KEEP_AS_KEYWORD and val.lower() not in existing_kw:
                    keywords.append(val)
                    existing_kw.add(val.lower())
                continue
        out.append(line)

    if keywords:
        # inject into domain_keyword_set or create one
        text = "\n".join(out)
        if "domain_keyword_set:" in text:
            new_out: list[str] = []
            injected = False
            for line in out:
                new_out.append(line)
                if not injected and line.strip() == "domain_keyword_set:":
                    for k in sorted(keywords, key=str.lower):
                        new_out.append(f"  - {k}")
                    injected = True
            out = new_out
        else:
            # after no_resolve / before first set
            insert_at = 0
            for i, line in enumerate(out):
                if line.strip() == "no_resolve: true":
                    insert_at = i + 1
                    break
            block = ["domain_keyword_set:"] + [f"  - {k}" for k in sorted(keywords, key=str.lower)]
            out = out[:insert_at] + block + out[insert_at:]

    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{path.name}: removed {len(removed)} bare suffixes, keywords+={len(keywords)}")
    print(f"  removed sample: {removed[:20]}")


def main() -> None:
    found = False
    for d in CANDIDATE_DIRS:
        for name in TARGETS:
            p = d / name
            if p.is_file():
                found = True
                sanitize(p)
    if not found:
        raise SystemExit("no ProxyGFW.yaml / Proxy.yaml under Egern/Routing or Routing")


if __name__ == "__main__":
    main()
