import re
from html.parser import HTMLParser

import requests


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "svg", "noscript"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "svg", "noscript"}:
            self.skip_depth = max(0, self.skip_depth - 1)

    def handle_data(self, data):
        if self.skip_depth == 0 and data and data.strip():
            cleaned = re.sub(r"\s+", " ", data).strip()
            if cleaned:
                self.parts.append(cleaned)

    def get_text(self):
        return " ".join(self.parts)


def extract_readable_text(html: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html)
    parser.close()
    return parser.get_text()


def web_scrape(url: str) -> str:
    print(f"🛠️  Executing tool: web_scrape({url})")
    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
        text = extract_readable_text(response.text)
        snippet = text[:2000].strip()
        return (
            f"Observation: Scraped page successfully from {url}.\n"
            f"Readable content preview:\n{snippet or 'No readable text found.'}"
        )
    except Exception as exc:
        return f"Observation: Error scraping page: {exc}"
