"""Bounded, same-host HTML crawler."""
from collections import deque
from html.parser import HTMLParser
from urllib.robotparser import RobotFileParser
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .parser import PageParser
from .safety import UnsafeTarget, validate_public_url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(NoRedirect())


def normalized(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    return parsed._replace(fragment="", query="", path=path).geturl().rstrip("/") or f"{parsed.scheme}://{parsed.netloc}/"


def fetch(url: str, timeout: float = 8.0):
    validate_public_url(url)
    request = Request(url, headers={"User-Agent": "SiteSentry/1.0 (+https://github.com/damnsunnyy/SiteSentry)", "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
    try:
        with OPENER.open(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                body = body[:2_000_000]
            return response.status, response.geturl(), content_type, body
    except HTTPError as exc:
        return exc.code, exc.geturl(), exc.headers.get_content_type() if exc.headers else "", b""
    except URLError as exc:
        raise ConnectionError(str(exc.reason)) from exc


def crawl(start_url: str, max_pages: int = 20, timeout: float = 8.0):
    start_url = validate_public_url(start_url)
    origin = urlparse(start_url)
    host = origin.hostname.lower()
    robots_url = f"{origin.scheme}://{origin.netloc}/robots.txt"
    robots = RobotFileParser(robots_url)
    try:
        robots_status, _, _, robots_body = fetch(robots_url, timeout)
        if robots_status in {401, 403} or robots_status >= 500 or 300 <= robots_status < 400:
            robots.parse(["User-agent: *", "Disallow: /"])
        elif robots_status < 400:
            robots.parse(robots_body.decode("utf-8", errors="replace").splitlines())
        else:
            robots.parse([])
    except (ConnectionError, UnsafeTarget, TimeoutError, OSError, ValueError):
        robots.parse(["User-agent: *", "Disallow: /"])
    queue = deque([normalized(start_url)])
    visited = set()
    pages = []
    robots_blocked = 0
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)
        if not robots.can_fetch("SiteSentry", url):
            robots_blocked += 1
            continue
        try:
            status, final_url, content_type, body = fetch(url, timeout)
            page_url = normalized(final_url)
            if urlparse(page_url).hostname != host:
                pages.append({"url": url, "status": status, "error": "Redirect left the starting host; stopped safely.", "parser": None})
                continue
            if "html" not in content_type.lower():
                pages.append({"url": page_url, "status": status, "error": f"Skipped non-HTML content ({content_type or 'unknown type'}).", "parser": None})
                continue
            parser = PageParser(page_url)
            parser.feed(body.decode("utf-8", errors="replace"))
            parser.close()
            parser.finish()
            pages.append({"url": page_url, "status": status, "error": "" if status < 400 else f"HTTP {status}", "parser": parser})
            if status < 400:
                for link in parser.links:
                    target, _ = urldefrag(link["href"])
                    target = normalized(target)
                    parsed = urlparse(target)
                    if parsed.scheme in {"http", "https"} and parsed.hostname == host and target not in visited and target not in queue and robots.can_fetch("SiteSentry", target):
                        queue.append(target)
        except (ConnectionError, UnsafeTarget, TimeoutError, OSError, ValueError) as exc:
            pages.append({"url": url, "status": 0, "error": str(exc), "parser": None})
    return pages, len(queue), robots_blocked, robots
