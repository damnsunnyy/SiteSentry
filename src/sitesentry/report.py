"""Readable console and self-contained HTML reports."""
from collections import Counter
from datetime import datetime, timezone
from html import escape


SEVERITY = {"critical": 0, "warning": 1, "notice": 2}


def summary(findings):
    counts = Counter(f.severity for f in findings)
    return {"critical": counts["critical"], "warning": counts["warning"], "notice": counts["notice"]}


def html_report(target, pages, findings, score, pending=0):
    counts = summary(findings)
    page_rows = "".join(f'<tr><td><a href="{escape(p["url"], quote=True)}">{escape(p["url"])}</a></td><td>{p["status"] or "—"}</td><td>{escape(p["error"] or "OK")}</td></tr>' for p in pages)
    finding_cards = []
    for finding in sorted(findings, key=lambda item: SEVERITY.get(item.severity, 3)):
        finding_cards.append(f'''<article class="finding {escape(finding.severity)}"><div class="finding-top"><span class="tag">{escape(finding.severity.upper())}</span><code>{escape(finding.rule)}</code></div><h3>{escape(finding.title)}</h3><p>{escape(finding.message)}</p><div class="fix"><b>FIX</b> {escape(finding.fix)}</div><a class="page-link" href="{escape(finding.page, quote=True)}">{escape(finding.page)}</a></article>''')
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    no_findings = '<div class="empty">No findings for this scan. Keep the good habits.</div>' if not finding_cards else "".join(finding_cards)
    remaining = f'<p class="notice">Crawl limit reached with {pending} page(s) still queued. Raise --max-pages to inspect more of this site.</p>' if pending else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>SiteSentry report · {escape(target)}</title><style>
:root{{--bg:#101411;--panel:#171e18;--line:#2b372d;--text:#edf1e8;--muted:#a4b09f;--acid:#c2ef66;--red:#ff927d;--orange:#f0bd68;--blue:#92c9e6}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,sans-serif}}header,main,footer{{max-width:1040px;margin:auto;padding:28px 22px}}header{{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);font:12px ui-monospace,monospace;color:var(--muted)}}header b{{color:var(--acid)}}.intro{{padding-top:54px}}.eyebrow,.tag,code,.metric span,.fix b{{font:10px ui-monospace,monospace;letter-spacing:.09em}}.eyebrow{{color:var(--acid)}}h1{{font-size:clamp(34px,7vw,62px);letter-spacing:-.06em;line-height:1.02;margin:12px 0}}.target{{color:var(--muted);overflow-wrap:anywhere}}.score-wrap{{display:flex;align-items:center;gap:20px;margin:34px 0}}.score{{width:94px;height:94px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(closest-side,var(--bg) 77%,transparent 79%),conic-gradient(var(--acid) {score}%,#ffffff18 0);font-size:28px;font-weight:600;color:var(--acid)}}.score-copy b{{display:block;font-size:16px}}.score-copy span{{color:var(--muted);font-size:12px}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.metric,.finding,.pages{{border:1px solid var(--line);background:var(--panel)}}.metric{{padding:17px}}.metric span{{display:block;color:var(--muted)}}.metric b{{display:block;font-size:29px;margin-top:7px}}.metric.critical b{{color:var(--red)}}.metric.warning b{{color:var(--orange)}}.metric.notice b{{color:var(--blue)}}h2{{margin:44px 0 15px;font-size:20px;letter-spacing:-.03em}}.finding-grid{{display:grid;gap:10px}}.finding{{padding:18px;border-left:3px solid #83917e}}.finding.critical{{border-left-color:var(--red)}}.finding.warning{{border-left-color:var(--orange)}}.finding.notice{{border-left-color:var(--blue)}}.finding-top{{display:flex;justify-content:space-between;gap:10px;color:var(--muted)}}.finding.critical .tag{{color:var(--red)}}.finding.warning .tag{{color:var(--orange)}}.finding.notice .tag{{color:var(--blue)}}h3{{font-size:16px;margin:10px 0 6px}}.finding p{{color:var(--muted);margin:0 0 13px;font-size:13px}}.fix{{padding:12px;background:#0e130f;color:#cbd4c5;font-size:13px}}.fix b{{color:var(--acid);margin-right:7px}}.page-link{{display:block;margin-top:11px;color:#8d9a88;font:10px ui-monospace,monospace;overflow-wrap:anywhere}}.pages{{width:100%;border-collapse:collapse;font-size:12px}}.pages th,.pages td{{padding:11px;text-align:left;border-bottom:1px solid var(--line);overflow-wrap:anywhere}}.pages th{{color:var(--muted);font:10px ui-monospace,monospace}}.pages a{{color:var(--acid)}}.empty,.notice{{padding:20px;color:var(--muted);background:var(--panel)}}.notice{{border-left:3px solid var(--orange)}}footer{{border-top:1px solid var(--line);color:#84917f;font:10px ui-monospace,monospace}}@media(max-width:600px){{.metrics{{grid-template-columns:1fr 1fr}}header{{font-size:10px}}.pages th:first-child,.pages td:first-child{{max-width:180px}}}}
</style></head><body><header><span><b>◉ SITESENTRY</b> / SITE QUALITY REPORT</span><span>GENERATED {generated}</span></header><main><section class="intro"><p class="eyebrow">WEB QUALITY · DISCOVERABILITY · ACCESSIBILITY</p><h1>A clearer view<br>of your site.</h1><p class="target">{escape(target)}</p><div class="score-wrap"><div class="score">{score}</div><div class="score-copy"><b>SiteSentry score</b><span>Starts at 100; deductions are transparent rule-of-thumb signals, not a certification.</span></div></div><div class="metrics"><div class="metric"><span>PAGES SCANNED</span><b>{len(pages)}</b></div><div class="metric critical"><span>CRITICAL</span><b>{counts["critical"]}</b></div><div class="metric warning"><span>WARNINGS</span><b>{counts["warning"]}</b></div><div class="metric notice"><span>NOTICES</span><b>{counts["notice"]}</b></div></div>{remaining}</section><h2>Findings</h2><section class="finding-grid">{no_findings}</section><h2>Scanned pages</h2><table class="pages"><thead><tr><th>PAGE</th><th>HTTP</th><th>RESULT</th></tr></thead><tbody>{page_rows}</tbody></table></main><footer>SiteSentry · Explainable baseline checks · {len(findings)} finding(s)</footer></body></html>'''


def console_report(target, pages, findings, score, pending=0):
    counts = summary(findings)
    print(f"\nSiteSentry · {target}\nScore: {score}/100 · {len(pages)} page(s) scanned · {len(findings)} finding(s)")
    print(f"Critical: {counts['critical']}   Warnings: {counts['warning']}   Notices: {counts['notice']}")
    for finding in sorted(findings, key=lambda item: SEVERITY.get(item.severity, 3)):
        print(f"\n[{finding.severity.upper()}] {finding.title} ({finding.rule})")
        print(f"  {finding.page}\n  {finding.message}\n  Fix: {finding.fix}")
    for page in pages:
        if page["error"]:
            print(f"\n[PAGE] {page['status'] or 'ERR'} {page['url']} — {page['error']}")
    if pending:
        print(f"\nCrawl limit reached with {pending} page(s) queued; raise --max-pages to inspect more.")
