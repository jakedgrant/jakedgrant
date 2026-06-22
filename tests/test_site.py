"""Invariant checks for the SmartFilter promotional site (docs/smartfilter/).

The site is static HTML/CSS/JS hosted via GitHub Pages at jakegrant.dev/smartfilter/.
These tests guard the things that silently break hosting or the download flow when the
pages are edited: link/asset integrity, in-page anchors, the Apple Smart App Banner,
App Store ID consistency, the canonical/social URLs, and Jekyll passthrough
(no YAML front-matter, no Liquid) so Pages serves the HTML verbatim instead of wrapping
it in the portfolio theme.

Zero third-party dependencies — standard library only. Run with:

    python3 -m unittest discover -s tests -v
"""

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

# Canonical values. APP_STORE_ID is the SmartFilter app's `SFAppStoreIdentifier`
# (SmartFilter/Info.plist in the app repo); hardcoded here because the app source
# lives in a separate repository.
APP_STORE_ID = "1271258894"
SITE_BASE = "https://jakegrant.dev/smartfilter/"
SUPPORT_EMAIL = "smartfilterapp@gmail.com"

SITE_DIR = Path(__file__).resolve().parent.parent / "docs" / "smartfilter"
PAGES = ("index.html", "privacy.html")

_EXTERNAL_PREFIXES = ("http://", "https://", "//", "mailto:", "tel:", "data:")


class _Page(HTMLParser):
    """Collects the bits of an HTML page the tests assert against."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metas = []            # list of attr dicts for <meta>
        self.links = []            # list of attr dicts for <link>
        self.refs = []             # hrefs/srcs from <a>/<link>/<img>/<script>/<source>
        self.ids = set()
        self._title = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        d = {k: (v or "") for k, v in attrs}
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "meta":
            self.metas.append(d)
        elif tag == "link":
            self.links.append(d)
            if d.get("href"):
                self.refs.append(d["href"])
        elif tag == "title":
            self._in_title = True
        if tag in ("a", "img", "script", "source"):
            for attr in ("href", "src"):
                if d.get(attr):
                    self.refs.append(d[attr])

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self._title.append(data)

    @property
    def title(self):
        return "".join(self._title).strip()

    def meta(self, key):
        for m in self.metas:
            if m.get("name") == key or m.get("property") == key:
                return m.get("content")
        return None

    def link(self, rel):
        for link in self.links:
            if link.get("rel") == rel:
                return link.get("href")
        return None


def _is_local(url):
    u = url.strip()
    return bool(u) and not u.lower().startswith(_EXTERNAL_PREFIXES) and not u.startswith("#")


class SiteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = {}
        cls.pages = {}
        for name in PAGES:
            path = SITE_DIR / name
            assert path.is_file(), f"missing page: {path}"
            text = path.read_text(encoding="utf-8")
            cls.raw[name] = text
            page = _Page()
            page.feed(text)
            cls.pages[name] = page
        cls.index = cls.pages["index.html"]
        cls.privacy = cls.pages["privacy.html"]

    # 1. Pages exist and parse, with content.
    def test_pages_present_and_nonempty(self):
        for name in PAGES:
            self.assertGreater(len(self.raw[name]), 500, f"{name} looks empty")
            self.assertTrue(self.pages[name].title, f"{name} has no <title>")

    # 2. Every relative href/src resolves to a file on disk.
    def test_local_links_resolve(self):
        for name, page in self.pages.items():
            for url in page.refs:
                if not _is_local(url):
                    continue
                rel = url.split("#", 1)[0].split("?", 1)[0]
                if not rel:
                    continue
                target = SITE_DIR / rel
                self.assertTrue(
                    target.exists(), f"{name}: broken local reference {url!r} -> {target}"
                )

    # 3. Every in-page anchor points at an existing id= in the right page.
    def test_anchors_resolve(self):
        for name, page in self.pages.items():
            for url in page.refs:
                if "#" not in url:
                    continue
                file_part, frag = url.split("#", 1)
                if not frag:
                    continue
                if file_part == "":
                    target_ids = page.ids
                else:
                    if not _is_local(file_part):
                        continue
                    target = self.pages.get(file_part.split("?", 1)[0])
                    if target is None:
                        continue  # file existence covered by test_local_links_resolve
                    target_ids = target.ids
                self.assertIn(
                    frag, target_ids, f"{name}: anchor #{frag} ({url!r}) has no matching id"
                )

    # 4. Smart App Banner present and well-formed (Apple spec).
    def test_smart_app_banner(self):
        content = self.index.meta("apple-itunes-app")
        self.assertIsNotNone(content, "index.html missing apple-itunes-app meta tag")
        m = re.fullmatch(r"app-id=(\d+)", content.strip())
        self.assertIsNotNone(m, f"malformed Smart App Banner content: {content!r}")
        self.assertEqual(m.group(1), APP_STORE_ID)

    # 5. Every App Store reference uses the same (correct) app id.
    def test_app_store_id_consistency(self):
        found = set()
        for text in self.raw.values():
            found.update(re.findall(r"apps\.apple\.com/app/id(\d+)", text))
        banner = self.index.meta("apple-itunes-app") or ""
        found.update(re.findall(r"app-id=(\d+)", banner))
        self.assertTrue(found, "no App Store references found on the site")
        self.assertEqual(
            found, {APP_STORE_ID}, f"inconsistent App Store IDs: {sorted(found)}"
        )

    # 6. Canonical + social URLs are absolute and point at the deployed path.
    def test_canonical_and_social_urls(self):
        self.assertEqual(self.index.link("canonical"), SITE_BASE)
        self.assertEqual(self.index.meta("og:url"), SITE_BASE)
        for key in ("og:image", "twitter:image"):
            value = self.index.meta(key)
            self.assertIsNotNone(value, f"missing {key}")
            self.assertTrue(
                value.startswith(SITE_BASE), f"{key} not under {SITE_BASE}: {value!r}"
            )

    # 7. Essential SEO/meta present.
    def test_essential_meta(self):
        for key in ("description", "viewport", "theme-color"):
            self.assertTrue(self.index.meta(key), f"index.html missing meta {key}")

    # 8. No YAML front-matter -> GitHub Pages serves the HTML verbatim.
    def test_no_jekyll_front_matter(self):
        for name in PAGES:
            self.assertFalse(
                self.raw[name].lstrip().startswith("---"),
                f"{name} starts with YAML front-matter; Jekyll would wrap it in the theme",
            )

    # 9. No Liquid syntax anywhere -> nothing for Jekyll to choke on.
    def test_no_liquid_tokens(self):
        for path in SITE_DIR.rglob("*"):
            if path.suffix.lower() not in (".html", ".css", ".js"):
                continue
            body = path.read_text(encoding="utf-8")
            self.assertNotIn("{{", body, f"Liquid token in {path}")
            self.assertNotIn("{%", body, f"Liquid token in {path}")

    # 10. Privacy page is wired back to the site and shows support contact.
    def test_privacy_page_wiring(self):
        files = {r.split("#", 1)[0].split("?", 1)[0] for r in self.privacy.refs}
        self.assertIn("index.html", files, "privacy.html does not link back to index.html")
        self.assertIn(SUPPORT_EMAIL, self.raw["privacy.html"])


if __name__ == "__main__":
    unittest.main()
