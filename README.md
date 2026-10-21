# SiteSentry

**Live demo:** [https://damnsunnyy.github.io/SiteSentry/](https://damnsunnyy.github.io/SiteSentry/)

**An explainable website quality scanner that produces a report you can act on.** SiteSentry crawls a small part of a public website, checks baseline HTML accessibility and discoverability signals, and exports a self-contained HTML or JSON report.

## Interactive browser demo

Try the [live SiteSentry demo](https://damnsunnyy.github.io/SiteSentry/). Paste HTML, choose a built-in example, or open a local `.html` file to get an interactive audit and downloadable report. The browser demo analyzes the HTML you provide; it does not fetch arbitrary URLs. Use the Python CLI below to crawl an allowed public website. Browser analysis stays on your device.

## The idea

A useful audit should tell you what it saw, why it flagged something, and how to improve it. SiteSentry keeps a small, transparent rule set instead of presenting an opaque score as a compliance certificate.

## What it checks

- Page title presence and practical title length
- Meta description presence and practical length
- Document language, mobile viewport, and canonical link
- A single descriptive page-level heading and heading order
- Missing image alt attributes, while allowing `alt=""` for decorative images
- Generic link names such as “click here”
- Form fields without a label or accessible name
- Main and navigation landmarks
- HTTP failures while crawling
- Optional broken internal links with `--check-links`

Every finding includes a stable rule ID, severity, page URL, explanation, and a suggested fix. The score starts at 100 and uses small, documented deductions; it is a rough triage aid and is not an accessibility or search ranking certification.

## Quick start

Requires Python 3.10 or later. SiteSentry uses only the Python standard library.

Install from a clone:

```bash
python -m pip install .
```

Scan a public site:

```bash
sitesentry https://example.com
```

Create a shareable HTML report and optionally fail a CI job when the score falls below a threshold:

```bash
sitesentry https://example.com --max-pages 30 --check-links --format html --output report.html --fail-below 75
```

Export JSON for another tool to process:

```bash
sitesentry https://example.com --format json --output report.json
```

Run without installing:

```bash
PYTHONPATH=src python -m sitesentry https://example.com --format html --output report.html
```

## Crawl boundaries and privacy

SiteSentry only requests public HTTP(S) pages on the starting host, follows links within that host, and respects `robots.txt`. It has no login flow, never submits forms, and does not send data to a third-party service. Localhost, private, reserved, and credential-bearing URLs are rejected. Redirects are not followed; this prevents a public page from redirecting the scanner to a private destination. The default crawl limit is 20 pages; `--max-pages` is capped at 200. Link checking is opt-in and checks at most 100 unique internal links with bounded concurrency.

Run scans only on websites you own or are allowed to inspect. The `examples/site/` directory contains sample HTML to illustrate what the checks look for; it is not uploaded or scanned by the CLI.

## Rule catalog and design

See [the rule catalog](docs/rules.md) for rule IDs, severity, and known limits. The scanner is intentionally dependency-free: `HTMLParser` inventories markup, a same-host crawler follows links, and the report generator creates one portable HTML file.

## Project layout

```text
src/sitesentry/
  parser.py   HTML inventory
  safety.py   Public URL and address checks
  fetch.py    HTTP fetch and robots-aware crawl
  rules.py    Finding definitions and score
  report.py   Terminal and self-contained HTML reports
  cli.py      Arguments, crawl orchestration, JSON output
examples/site/  small illustrative HTML pages
```

## License

MIT. See [LICENSE](LICENSE).
