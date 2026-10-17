# SiteSentry rule catalog

These rules catch common baseline issues visible in fetched HTML. They do not inspect rendered CSS, JavaScript state, keyboard behavior, image meaning, or assistive-technology output. A clear report is a starting point for review, not proof of conformance.

| Rule ID | Severity | What it checks | Suggested response |
| --- | --- | --- | --- |
| `http.status` | Critical | A page failed to return a successful response | Check the URL, hosting configuration, and response status |
| `html.lang` | Warning | Root `<html>` has no language | Set a correct `lang` attribute |
| `seo.title.missing` | Critical | Document title is absent | Add a descriptive title |
| `seo.title.length` | Notice | Title is unusually short or long | Write a specific title, roughly 15–60 characters |
| `seo.description.missing` | Warning | Search description is absent | Add a page-specific meta description |
| `seo.description.length` | Notice | Description is unusually short or long | Summarize the page in roughly 50–170 characters |
| `content.h1.missing` | Warning | No non-empty page-level heading exists | Add one descriptive `<h1>` |
| `content.h1.multiple` | Notice | More than one non-empty `<h1>` was found | Review the heading outline and use one page-level heading |
| `content.heading.skip` | Notice | Heading levels skip a level | Keep heading nesting sequential |
| `a11y.image.alt` | Critical | An image lacks an `alt` attribute | Describe informative images; use an empty value for decorative images |
| `a11y.link.name` | Warning | A link uses generic text such as “here” | Name its destination or action |
| `a11y.form.label` | Critical | A form field has no associated label or accessible name | Add a `<label>` or accessible name |
| `a11y.landmarks` | Notice | Neither `<main>` nor `<nav>` was found | Add landmarks for primary content and navigation |
| `mobile.viewport` | Warning | A viewport declaration is absent | Add a mobile viewport meta tag |
| `seo.canonical.missing` | Notice | No canonical link is declared | Declare the preferred URL when the page needs one |
| `link.internal.broken` | Warning | An opt-in internal-link request failed | Repair the link or restore the destination |
| `crawl.robots` | Notice | Some URLs were withheld by site policy or robots could not be read | Respect the policy; contact the owner for permission |

## Score

Each critical finding subtracts 18 points, each warning 8, and each notice 3. The score is clamped to 0–100. Repeated findings count independently, so a sitewide template issue can lower the score substantially. This simple scale exists to help compare a site's own follow-up scans; it is not a standards pass/fail grade.
