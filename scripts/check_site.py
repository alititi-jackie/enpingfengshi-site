"""Verify published resources, anchors, paginated originals and sitemap."""
from collections import defaultdict
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from xml.etree import ElementTree as ET

ROOT = Path('site')
ORIGIN = 'https://enping.fengshizupu.com'
COUNT = json.loads(Path('data/book-pagination.json').read_text())['scanCount']


def scans_valid():
    folder = ROOT / 'pages'
    names = {f'p{page:04d}.webp' for page in range(1, COUNT + 1)}
    return folder.is_dir() and {p.name for p in folder.glob('*.webp')} == names and all(
        valid_webp(folder / name) for name in names)


def valid_webp(path):
    with path.open('rb') as image:
        header = image.read(12)
    return header[:4] == b'RIFF' and header[8:12] == b'WEBP'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = set()
        self.noindex = False
        self.canonical = None
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'meta' and attrs.get('name') == 'robots':
            self.noindex = 'noindex' in attrs.get('content', '')
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        for key in ('href', 'src', 'data-image', 'data-search-index'):
            value = attrs.get(key, '')
            if value.startswith('/') and not value.startswith('//'):
                self.links.add(value)


def local_target(path):
    target = ROOT / unquote(path).lstrip('/')
    return target / 'index.html' if target.is_dir() else target


def check_site(*, require_scans=True):
    if require_scans and not scans_valid():
        raise SystemExit('Expected a complete set of valid original book scans')
    pages = {p: Page(p) for p in ROOT.rglob('*.html')}
    links = defaultdict(set)
    for path, page in pages.items():
        for link in page.links:
            links[link].add(path)
    home_index = ROOT / 'assets/search-index.json'
    search = json.loads(home_index.read_text(encoding='utf-8'))
    scoped_pages = [row for section in search['scopedPages'].values() for row in section.values()]
    for row in [*search['original'], *search['editions'], *search['numeric'].values(), *scoped_pages]:
        links[row['url']].add(home_index)
    for edition in search['editions']:
        index = local_target(urlsplit(edition['pageIndex']).path)
        for row in json.loads(index.read_text(encoding='utf-8')).values():
            links[row['url']].add(index)
    for index_url in search['people']:
        index = local_target(urlsplit(index_url).path)
        for row in json.loads(index.read_text(encoding='utf-8')):
            links[row['url']].add(index)
    for link, parents in links.items():
        url = urlsplit(link)
        target = local_target(url.path)
        if not target.is_file() and (require_scans or not url.path.startswith('/pages/')):
            raise SystemExit(f'Broken link {link} from {next(iter(parents))}')
        if url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            raise SystemExit(f'Broken anchor {link}')
        if url.path == '/reader.html' and 'p' in parse_qs(url.query):
            page = parse_qs(url.query)['p'][0]
            if not page.isdecimal() or not 1 <= int(page) <= COUNT:
                raise SystemExit(f'Invalid scan sequence: {link}')
    sitemap = [e.text for e in ET.parse(ROOT / 'sitemap.xml').iter() if e.tag.endswith('}loc')]
    if len(sitemap) != len(set(sitemap)):
        raise SystemExit('Duplicate sitemap URL')
    for url in sitemap:
        page = pages.get(local_target(urlsplit(url).path))
        if not page or page.noindex or page.canonical != url or not url.startswith(ORIGIN + '/'):
            raise SystemExit(f'Invalid sitemap URL: {url}')
    print(f'Checked {len(pages)} pages, {len(links)} internal targets, {len(sitemap)} sitemap URLs')


if __name__ == '__main__':
    import sys

    if '--scans-only' in sys.argv:
        if not scans_valid():
            raise SystemExit('Incomplete original scans')
    else:
        check_site(require_scans='--without-scans' not in sys.argv)
