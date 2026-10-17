"""Small, dependency-free HTML inventory for SiteSentry."""
from html.parser import HTMLParser
from urllib.parse import urljoin


class PageParser(HTMLParser):
    def __init__(self, page_url: str):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.title = ""
        self.description = ""
        self.language = ""
        self.viewport = False
        self.canonical = ""
        self.headings: list[tuple[int, str]] = []
        self.images: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.forms: list[dict[str, object]] = []
        self.landmarks: set[str] = set()
        self._title_depth = 0
        self._description_found = False
        self._heading_depth = 0
        self._heading_text = ""
        self._link: dict[str, str] | None = None
        self._form: dict[str, object] | None = None
        self._label_depth = 0
        self._label_for = ""
        self.labels: set[str] = set()
        self._input_index = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang", "").strip()
        elif tag == "title":
            self._title_depth += 1
        elif tag == "meta":
            name = attrs.get("name", "").lower()
            if name == "description" and not self._description_found:
                self.description = attrs.get("content", "").strip()
                self._description_found = True
            elif name == "viewport":
                self.viewport = bool(attrs.get("content", "").strip())
        elif tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = urljoin(self.page_url, attrs.get("href", ""))
        elif tag in {"main", "nav", "header", "footer", "aside"}:
            self.landmarks.add(tag)
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._heading_depth = int(tag[1])
            self._heading_text = ""
        elif tag == "img":
            self.images.append({"src": urljoin(self.page_url, attrs.get("src", "")), "alt": attrs.get("alt", ""), "decorative": "alt" in attrs and not attrs.get("alt", "").strip()})
        elif tag == "a":
            self._link = {"href": urljoin(self.page_url, attrs.get("href", "")), "text": "", "rel": attrs.get("rel", "")}
        elif tag == "form":
            self._form = {"fields": [], "label_ids": []}
        elif tag == "label":
            self._label_depth = 1
            self._label_for = attrs.get("for", "")
        elif self._form is not None and tag in {"input", "select", "textarea"}:
            if tag == "input" and attrs.get("type", "").lower() in {"hidden", "submit", "button", "reset", "image"}:
                return
            self._input_index += 1
            field_id = attrs.get("id", "")
            self._form["fields"].append({"id": field_id, "name": attrs.get("name", ""), "type": attrs.get("type", tag), "labelled": bool(self._label_depth) or bool(field_id and field_id in self.labels) or bool(attrs.get("aria-label", "").strip()) or bool(attrs.get("aria-labelledby", "").strip())})
        if self._label_depth:
            self._label_depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self._title_depth:
            self._title_depth = 0
        elif tag == "label" and self._label_depth:
            self._label_depth = 0
            if self._label_for:
                self.labels.add(self._label_for)
            self._label_for = ""
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._heading_depth:
            self.headings.append((self._heading_depth, " ".join(self._heading_text.split())))
            self._heading_depth = 0
        elif tag == "a" and self._link is not None:
            self.links.append(self._link)
            self._link = None
        elif tag == "form" and self._form is not None:
            self.forms.append(self._form)
            self._form = None

    def handle_data(self, data):
        if self._title_depth:
            self.title += data
        if self._heading_depth:
            self._heading_text += data
        if self._link is not None:
            self._link["text"] += data

    def finish(self):
        self.title = " ".join(self.title.split())
        return self
