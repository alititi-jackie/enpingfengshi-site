"""Publish small search forms backed by shared JSON indexes."""
from hashlib import sha256
from html import escape
import json


def publish_index(write, path, rows):
    content = json.dumps(rows, ensure_ascii=False, separators=(',', ':'))
    write(path, content)
    return f'/{path}?v={sha256(content.encode()).hexdigest()[:12]}'


def indexed_search(index_url, *, home=False, toc=False, browse=False, page_index=None):
    field = 'q' if home else 'tq' if toc else 'editionName'
    button = ' id="go"' if home else ''
    kind = 'home' if home else 'toc' if toc else 'people'
    hint = '输入村名、房支、书页码或新版姓名' if home else '输入姓名或编号'
    if toc:
        hint = '输入原书页码、章节、村名或房支'
    page_attribute = ''
    if page_index:
        hint = '输入姓名、人物编号（如 p15）或谱页页码'
        page_attribute = f' data-page-index="{escape(page_index)}"'
    results = 'searchResults' if home or toc else 'editionSearchResults'
    all_button = '<p><button type="button" class="btn ghost" data-list-all form="editionPersonSearch">查看全部姓名</button></p>' if browse else ''
    return (
        f'<form class="searchbox" id="editionPersonSearch" data-kind="{kind}" '
        f'data-search-index="{escape(index_url)}"{page_attribute} data-results="{results}" data-status="searchStatus">'
        f'<input id="{field}" name="q" type="search" placeholder="{hint}" aria-label="{hint}" autocomplete="off">'
        f'<button type="submit"{button}>搜索</button></form>{all_button}'
        '<div id="searchStatus" class="vcount" role="status"></div>'
        f'<div id="{results}" class="list"></div>'
        '<script defer src="/assets/search.js?v=4"></script>')
