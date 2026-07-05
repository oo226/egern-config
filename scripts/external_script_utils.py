"""Shared helpers for mirroring third-party script URLs into this repository."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

from paths import GITHUB_RAW_MAIN, SIGNIN_SCRIPTS

EXTERNAL_SCRIPTS = SIGNIN_SCRIPTS / "_external"
REWRITE_MAP = Path(__file__).resolve().parent / "external-script-rewrites.yaml"

SCRIPT_PATH_RE = re.compile(r"script-path\s*=\s*([^\s,]+)", re.IGNORECASE)
LOCAL_MARKER = "oo226/egern-config"

SKIP_MIRROR_HOSTS = (
    "kelee.one",
    "perzikkop.com",
)

GITHUB_RELEASE_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$",
    re.IGNORECASE,
)
GITHUB_RAW_RE = re.compile(
    r"^https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$",
    re.IGNORECASE,
)
GIST_RAW_RE = re.compile(
    r"^https?://gist\.githubusercontent\.com/(.+)$",
    re.IGNORECASE,
)
GIST_PAGE_RE = re.compile(
    r"^https?://gist\.github\.com/([^/]+)/([0-9a-f]+)/raw/([0-9a-f]+)/(.+)$",
    re.IGNORECASE,
)


def is_local_url(url: str) -> bool:
    return LOCAL_MARKER in url


def should_skip_mirror(url: str) -> bool:
    host = urlparse(normalize_url(url)).netloc.lower()
    return any(skip in host for skip in SKIP_MIRROR_HOSTS)


def normalize_url(url: str) -> str:
    return unquote(url.strip().strip('"').strip("'"))


def local_raw_url(relative_posix: str) -> str:
    rel = relative_posix.lstrip("/")
    return f"{GITHUB_RAW_MAIN}/Scripts/_external/{rel}"


def dest_relative_path(url: str) -> str:
    """Map an external script URL to a stable path under Scripts/_external/."""
    url = normalize_url(url)
    parsed = urlparse(url)

    release = GITHUB_RELEASE_RE.match(url)
    if release:
        user, repo, tag, filename = release.groups()
        safe_tag = tag.replace("/", "_")
        return f"github-releases/{user}/{repo}/{safe_tag}/{filename}"

    raw = GITHUB_RAW_RE.match(url)
    if raw:
        user, repo, branch, rest = raw.groups()
        return f"github-raw/{user}/{repo}/{branch}/{rest}"

    if parsed.netloc.lower() == "github.com" and "/raw/" in parsed.path:
        # https://github.com/user/repo/raw/branch/path
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 4 and parts[2] == "raw":
            user, repo, branch = parts[0], parts[1], parts[3]
            rest = "/".join(parts[4:]) if len(parts) > 4 else parts[-1]
            return f"github-raw/{user}/{repo}/{branch}/{rest}"

    gist_page = GIST_PAGE_RE.match(url)
    if gist_page:
        user, gist_id, revision, filename = gist_page.groups()
        return f"gist/{user}/{gist_id}/{revision}/{filename}"

    gist = GIST_RAW_RE.match(url)
    if gist:
        return f"gist/{gist.group(1)}"

    host = parsed.netloc.lower().replace(":", "_")
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    suffix = PurePosixPath(parsed.path).name or "script.js"
    return f"by-host/{host}/{digest}/{suffix}"


def dest_absolute_path(url: str) -> Path:
    return EXTERNAL_SCRIPTS / dest_relative_path(url)


def extract_script_urls(text: str) -> set[str]:
    urls: set[str] = set()
    for match in SCRIPT_PATH_RE.finditer(text):
        url = normalize_url(match.group(1))
        if url.startswith("http") and not is_local_url(url):
            urls.add(url)
    return urls


def collect_script_urls_from_paths(paths: list[Path]) -> set[str]:
    found: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        found.update(extract_script_urls(text))
    return found


def collect_module_source_paths(root: Path) -> list[Path]:
    patterns = ("*.module", "*.sgmodule")
    paths: list[Path] = []
    modules = root / "Modules"
    if not modules.is_dir():
        return paths
    for pattern in patterns:
        paths.extend(modules.glob(pattern))
        upstream = modules / "_upstream"
        if upstream.is_dir():
            paths.extend(upstream.rglob(pattern))
    return sorted(set(paths))


def apply_external_rewrites(text: str, rewrites: dict[str, str]) -> str:
    if not rewrites:
        return text
    for old in sorted(rewrites, key=len, reverse=True):
        if old in text:
            text = text.replace(old, rewrites[old])
    return text


def load_rewrite_map(path: Path = REWRITE_MAP) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rewrites = data.get("rewrites") or {}
    return {str(k): str(v) for k, v in rewrites.items()}
