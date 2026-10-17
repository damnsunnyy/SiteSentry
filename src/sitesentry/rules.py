"""Explainable, small checks for basic discoverability and accessibility."""
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass
class Finding:
    rule: str
    severity: str
    title: str
    message: str
    page: str
    fix: str

    def as_dict(self):
        return asdict(self)


def audit_page(page):
    findings = []
    url, status, parser = page["url"], page["status"], page["parser"]

    def add(rule, severity, title, message, fix):
        findings.append(Finding(rule, severity, title, message, url, fix))

    if status == 0 or status >= 400:
        add("http.status", "critical", "Page did not load successfully", page["error"] or f"HTTP {status}", "Check the URL, hosting configuration, and server response. Return the intended page with a successful HTTP status.")
    if parser is None:
        return findings
    if not parser.language:
        add("html.lang", "warning", "Document language is missing", "Screen readers need the document language to pronounce content correctly.", "Set a language on the root element, for example <html lang=\"en\">.")
    if not parser.title:
        add("seo.title.missing", "critical", "Page title is missing", "The browser tab and search result have no descriptive title.", "Add a concise, unique <title> in the document head.")
    elif len(parser.title) < 15 or len(parser.title) > 60:
        add("seo.title.length", "notice", "Page title may be hard to scan", f"The title has {len(parser.title)} characters; this check flags titles under 15 or over 60.", "Write a specific title that describes the page in roughly 15–60 characters.")
    if not parser.description:
        add("seo.description.missing", "warning", "Search description is missing", "Search engines may choose unrelated page text for the result snippet.", "Add a useful <meta name=\"description\" content=\"…\"> to the head.")
    elif len(parser.description) < 50 or len(parser.description) > 170:
        add("seo.description.length", "notice", "Search description length is unusual", f"The description has {len(parser.description)} characters; this check flags under 50 or over 170.", "Summarize the page clearly in approximately 50–170 characters.")
    h1s = [text for level, text in parser.headings if level == 1 and text]
    if not h1s:
        add("content.h1.missing", "warning", "No main heading was found", "A clear page heading helps people understand the page structure.", "Add one descriptive <h1> that names the page's main topic.")
    elif len(h1s) > 1:
        add("content.h1.multiple", "notice", "Several main headings were found", f"Found {len(h1s)} non-empty h1 headings.", "Use one clear page-level heading and nest section headings beneath it.")
    previous = 0
    for level, text in parser.headings:
        if text and previous and level > previous + 1:
            add("content.heading.skip", "notice", "Heading levels skip a step", f"Heading “{text[:55]}” jumps from h{previous} to h{level}.", "Keep heading levels in order so keyboard and screen reader users can navigate the outline.")
            break
        if text:
            previous = level
    missing_alt = [image for image in parser.images if not image["alt"].strip() and not image["decorative"]]
    if missing_alt:
        add("a11y.image.alt", "critical", "Images are missing alt attributes", f"{len(missing_alt)} of {len(parser.images)} images have no alt text attribute.", "Describe informative images with concise alt text. Use alt=\"\" only for decorative images.")
    vague = [link["text"].strip() for link in parser.links if link["href"] and link["text"].strip().lower() in {"click here", "here", "read more", "more", "link"}]
    if vague:
        add("a11y.link.name", "warning", "Some links lack clear names", f"Found {len(vague)} links with generic text such as “{vague[0]}”.", "Make link text describe its destination or purpose, including when read outside the surrounding paragraph.")
    if not parser.viewport:
        add("mobile.viewport", "warning", "Mobile viewport is not declared", "The page may render at a desktop width on phones.", "Add a viewport meta tag with width=device-width and initial-scale=1.")
    if not parser.canonical:
        add("seo.canonical.missing", "notice", "Canonical URL is not declared", "Duplicate URL variants can be harder for crawlers to consolidate.", "Add a rel=\"canonical\" link pointing to the preferred public URL.")
    if parser.forms:
        fields = [field for form in parser.forms for field in form["fields"]]
        unlabeled = sum(not field["labelled"] for field in fields)
        if unlabeled:
            add("a11y.form.label", "critical", "Form fields need accessible labels", f"{unlabeled} of {len(fields)} checked form fields have no associated label or accessible name.", "Associate a <label> with each field or provide a valid aria-label/aria-labelledby name.")
    if not ({"main", "nav"} & parser.landmarks):
        add("a11y.landmarks", "notice", "No main or navigation landmark found", "Landmarks provide useful keyboard and screen reader shortcuts.", "Wrap the primary content in <main> and navigation in <nav>.")
    return findings


def score_findings(findings):
    deductions = {"critical": 18, "warning": 8, "notice": 3}
    total = min(100, sum(deductions.get(item.severity, 0) for item in findings))
    return max(0, 100 - total)
