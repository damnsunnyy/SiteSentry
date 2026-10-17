"""Command-line interface for SiteSentry."""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urldefrag, urlparse

from .fetch import crawl, fetch, normalized
from .report import console_report, html_report
from .rules import audit_page, score_findings
from .safety import UnsafeTarget, validate_public_url


def check_internal_links(pages, robots, workers=8, limit=100):
    hosts = {urlparse(page["url"]).hostname for page in pages}
    unique = {}
    for page in pages:
        parser = page["parser"]
        if parser is None:
            continue
        for link in parser.links:
            target = normalized(urldefrag(link["href"])[0])
            if urlparse(target).hostname in hosts and target not in unique and robots.can_fetch("SiteSentry", target):
                unique[target] = link["text"].strip() or target
    targets = list(unique)[:limit]
    results = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(fetch, target, 6.0): target for target in targets}
        for future in as_completed(jobs):
            target = jobs[future]
            try:
                status, _, _, _ = future.result()
                results[target] = status
            except Exception as exc:
                results[target] = 0
    findings = []
    for target, status in results.items():
        if status == 0 or status >= 400:
            findings.append({"rule": "link.internal.broken", "severity": "warning", "title": "Internal link may be broken", "message": f"{unique[target]} returned HTTP {status or 'no response'}.", "page": target, "fix": "Correct the destination or restore the linked page."})
    return findings, max(0, len(unique) - len(targets))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sitesentry", description="Crawl a public website and find explainable HTML quality issues.")
    parser.add_argument("url", help="Starting public page URL (HTTP or HTTPS)")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum same-host HTML pages to inspect (default: 20; max: 200)")
    parser.add_argument("--timeout", type=float, default=8.0, help="Per-page network timeout in seconds (default: 8)")
    parser.add_argument("--check-links", action="store_true", help="Check up to 100 unique internal links for broken responses")
    parser.add_argument("--format", choices=("console", "html", "json"), default="console", help="Report output format")
    parser.add_argument("--output", type=Path, help="Write HTML or JSON output to this file")
    parser.add_argument("--fail-below", type=int, metavar="SCORE", help="Exit with status 1 when the score falls below SCORE")
    args = parser.parse_args(argv)
    if not 1 <= args.max_pages <= 200:
        parser.error("--max-pages must be between 1 and 200")
    if not 1 <= args.timeout <= 60:
        parser.error("--timeout must be between 1 and 60 seconds")
    if args.fail_below is not None and not 0 <= args.fail_below <= 100:
        parser.error("--fail-below must be between 0 and 100")
    try:
        target = validate_public_url(args.url)
        pages, pending, robots_blocked, robots = crawl(target, args.max_pages, args.timeout)
    except UnsafeTarget as exc:
        parser.error(str(exc))
    findings = [finding for page in pages for finding in audit_page(page)]
    skipped_links = 0
    if args.check_links:
        link_findings, skipped_links = check_internal_links(pages, robots)
        from .rules import Finding
        findings.extend(Finding(**finding) for finding in link_findings)
    if robots_blocked:
        from .rules import Finding
        findings.append(Finding("crawl.robots", "notice", "Some pages were withheld by site policy", f"{robots_blocked} discovered page(s) were excluded because robots.txt disallows access (or could not be checked safely).", pages[0]["url"] if pages else target, "Respect the site's crawl policy. Contact its owner if you need permission to inspect those URLs."))
    score = score_findings(findings) if pages else 0
    if args.format == "json":
        document = {"target": target, "score": score, "pages_scanned": len(pages), "queued_pages_not_scanned": pending, "pages_withheld_by_robots": robots_blocked, "links_skipped_by_limit": skipped_links, "findings": [finding.as_dict() for finding in findings], "pages": [{"url": page["url"], "status": page["status"], "error": page["error"]} for page in pages]}
        output = json.dumps(document, indent=2)
    elif args.format == "html":
        output = html_report(target, pages, findings, score, pending)
    else:
        console_report(target, pages, findings, score, pending)
        if args.output:
            parser.error("--output can be used with --format html or --format json")
        return int(args.fail_below is not None and score < args.fail_below)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output)
    return int(args.fail_below is not None and score < args.fail_below)


if __name__ == "__main__":
    sys.exit(main())
