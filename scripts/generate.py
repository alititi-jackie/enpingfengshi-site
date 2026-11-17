#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the Enping Feng genealogy book site into site/.

Inputs:
  data/toc.json  {"all": [{t,p,lvl}], "branches": [{id,t,p,end,zu,fang}]}
  assets/style.css, assets/icon.svg, favicon.svg
Page images (site/pages/pNNNN.webp, NNNN = PDF page 1..1301) are rendered
by the workflow before this script runs; this script does not touch them.
"""
import json, os, re, shutil, html
from hashlib import sha256
from urllib.parse import quote
from book_pagination import load_pagination
from search_markup import indexed_search, publish_index
from family_ui import reader_toolbar, FAB as SHARED_FAB, FAB_SCRIPT, asset_version
from village_editions import INDEX, build_editions, edition_path, edition_title, image_dialog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
PAGES, NUMERIC_LOOKUP, SECTION_LINKS = load_pagination(os.path.join(ROOT, 'data', 'book-pagination.json'))
BOOK_MAX = max(NUMERIC_LOOKUP)


def esc(s):
    return html.escape(str(s), quote=True)


def label_for_pdf(n):
    return PAGES[n]['label']

def reader_url(pdf_page):
    return f'/reader.html?p={pdf_page}'

def search_box(field, hint, count=None):
    status = f'<div class="vcount" id="{count}" role="status"></div>' if count else ''
    button = '' if count else '<button id="go" type="button">搜索</button>'
    return f'<div class="searchbox"><input id="{field}" type="text" placeholder="{esc(hint)}" aria-label="{esc(hint)}" autocomplete="off">{button}</div>{status}'


def entry(href, title, detail, attributes=''):
    return f'<a{attributes} href="{esc(href)}"><span>{esc(title)}</span><span class="pg">{esc(detail)}</span></a>'

ORIGIN = 'https://enping.fengshizupu.com'
THEME_FILE = os.path.join(ROOT, 'assets', 'genealogy-theme.css')
with open(THEME_FILE, 'rb') as theme:
    THEME_VERSION = sha256(theme.read()).hexdigest()[:12]


def head(title, desc, url, index):
    canonical = f'{ORIGIN}{url}' if url else ''
    canonical_tag = f'<link rel="canonical" href="{esc(canonical)}">' if canonical else ''
    robots = '' if index else '<meta name="robots" content="noindex">'
    og_url = f'<meta property="og:url" content="{esc(canonical)}">' if canonical else ''
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}
{canonical_tag}
<meta property="og:type" content="website">
<meta property="og:locale" content="zh_CN">
<meta property="og:site_name" content="恩平冯氏族谱">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{og_url}
<meta property="og:image" content="{ORIGIN}/assets/share-logo.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="480">
<meta property="og:image:height" content="480">
<meta property="og:image:alt" content="恩平冯氏族谱「冯」字标志">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{ORIGIN}/assets/share-logo.png">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/style.css?v={asset_version(ROOT, 'style.css')}">
<link rel="stylesheet" href="/assets/genealogy-theme.css?v={THEME_VERSION}">
<script src="/assets/site.js?v=2"></script>
</head>
<body class="site-theme">'''

def header(active=''):
    links = [('首页', 'https://fengshizupu.com/', 'main'), ('资讯', 'https://fengshizupu.com/news/', 'news'),
             ('族谱', 'https://fengshizupu.com/archives/', 'archives'), ('恩平', '/', 'home'),
             ('目录', '/toc.html', 'toc'), ('新谱', INDEX, 'editions')]
    parts = []
    for t, u, k in links:
        cls = ' class="on"' if k == active else ''
        parts.append(f'<a href="{u}"{cls}>{t}</a>')
    nav = ''.join(parts) + '<button class="share" type="button" onclick="sharePage()">分享</button>'
    return f'''<header class="brandbar"><div class="wrap">
<a class="brand" href="/"><img src="/assets/icon.svg" alt="冯" width="46" height="46"><span>恩平冯氏族谱<small>fengshizupu.com</small></span></a>
</div></header>
<nav class="mainnav"><div class="wrap mainnav-in">{nav}</div></nav>'''

FOOT = '''<footer class="site site-footer"><a href="https://fengshizupu.com/contribute/">宗亲投稿 · 宗亲共建</a><br>
恩平冯氏族谱 · 在线查阅<br>
<strong>本站原书版本 ·《恩平冯氏族谱》1995 年重修版</strong> · <a href="/buy.html">购买电子版</a><br>
全国数字族谱平台 · <a href="https://fengshizupu.com/">fengshizupu.com</a> · <a href="/about/">关于本站</a>
</footer>
</body></html>'''

FAB = SHARED_FAB + FAB_SCRIPT

def page(title, body, desc, active='', *, url=None, index=True):
    return head(title, desc, url, index) + header(active) + body + FAB + FOOT


def load_data():
    with open(os.path.join(ROOT, 'data', 'toc.json'), encoding='utf-8') as f:
        return json.load(f)

def build(data):
    os.makedirs(SITE, exist_ok=True)
    os.makedirs(os.path.join(SITE, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(SITE, 'branch'), exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'assets', 'site.js'), os.path.join(SITE, 'assets', 'site.js'))
    shutil.copy(os.path.join(ROOT, 'assets', 'style.css'), os.path.join(SITE, 'assets', 'style.css'))
    for asset in ('search.js', 'reader-controls.js', 'original-reader.js'):
        shutil.copy(os.path.join(ROOT, 'assets', asset), os.path.join(SITE, 'assets', asset))
    shutil.copy(THEME_FILE, os.path.join(SITE, 'assets', 'genealogy-theme.css'))
    shutil.copy(os.path.join(ROOT, 'assets', 'icon.svg'), os.path.join(SITE, 'assets', 'icon.svg'))
    shutil.copy(os.path.join(ROOT, 'favicon.svg'), os.path.join(SITE, 'favicon.svg'))
    shutil.copy(os.path.join(ROOT, 'assets', 'edition-reader.js'), os.path.join(SITE, 'assets', 'edition-reader.js'))
    shutil.copy(os.path.join(ROOT, 'assets', 'share-logo.png'), os.path.join(SITE, 'assets', 'share-logo.png'))
    import glob
    for vf in glob.glob(os.path.join(ROOT, 'baidu_verify_*.html')):
        shutil.copy(vf, os.path.join(SITE, os.path.basename(vf)))

    branches = data['branches']
    all_entries = data['all']
    by_id = {b['id']: b for b in branches}
    villages = {name: [by_id[i] for i in ids] for name, ids in data.get('villages', {}).items()}
    edition_results, person_indexes, edition_urls, updated_villages = build_editions(
        ROOT, SITE, page, w, entry, villages, reader_toolbar)
    updates_by_book_village = {}
    for editions in updated_villages.values():
        for edition in editions:
            updates_by_book_village.setdefault(edition.get('bookVillage'), []).append(edition)
    branch_villages = {}
    for name, bs in villages.items():
        for b in bs:
            branch_villages.setdefault(b['id'], []).append(name)

    village_aliases = {}
    for edition in edition_results:
        village = edition['bookVillage']
        village_aliases.setdefault(village, set()).update(edition['aliases'])

    def alias_keys(names):
        return ' '.join(sorted({alias for name in names for alias in village_aliases.get(name, ())}))

    # ---------- index ----------
    def page_result(title, scan, key=''):
        return {'t': title, 'k': key, 'url': reader_url(scan), 'detail': label_for_pdf(scan)}

    search_data = []
    for item in all_entries:
        if scan := item.get('pdf') or NUMERIC_LOOKUP.get(item.get('p')):
            search_data.append(page_result(item['t'], scan))
    for branch in branches:
        names = branch_villages.get(branch['id'], [])
        aliases = alias_keys(names)
        search_data.append({
            't': branch['t'], 'k': ' '.join([*names, aliases]),
            'url': f'/branch/{branch["id"]}.html',
            'detail': f'{branch.get("zu", "")} {branch.get("fang", "")} · {label_for_pdf(NUMERIC_LOOKUP[branch["p"]])}',
        })
    for name, refs in villages.items():
        search_data.append({
            't': name, 'k': alias_keys([name]),
            'url': f'/villages.html#{quote(name)}',
            'detail': '村庄 · ' + label_for_pdf(NUMERIC_LOOKUP[refs[0]['p']]),
        })
    for section, scan in SECTION_LINKS:
        search_data.append(page_result(section, scan))
    for scan in (3, 1299, 1300):
        search_data.append(page_result(label_for_pdf(scan), scan))
    scoped_pages = {}
    section_ordinals = {}
    for original in PAGES[1:]:
        section = original['section']
        section_ordinals[section] = section_ordinals.get(section, 0) + 1
        if section == '卷首':
            scoped_pages.setdefault(section, {})[section_ordinals[section]] = page_result(
                f"卷首第 {section_ordinals[section]} 张", original['scan'], original['label'])
        elif section.startswith('目录'):
            scoped_pages.setdefault(section, {})[original['printed']] = page_result(
                original['label'], original['scan'])
    homepage_index = publish_index(w, 'assets/search-index.json', {
        'original': search_data, 'editions': edition_results, 'people': person_indexes,
        'scopedPages': scoped_pages,
        'numeric': {number: page_result(label_for_pdf(scan), scan) for number, scan in NUMERIC_LOOKUP.items()},
    })
    zu_cards = ''
    for zu, desc in [('复春系', '九房 · 书第32–890页'), ('宁邦房', '一至二十世 · 书第891–977页'),
                     ('万辅祖', '一至十六世 · 书第978–1070页')]:
        first = next((b for b in branches if b.get('zu', '').startswith(zu[:2])), None)
        href = f"/branch/{first['id']}.html" if first else '/toc.html'
        zu_cards += f'<a class="card" href="{href}"><div class="big">{zu}</div><div class="small">{desc}</div></a>'
    body = f'''
<div class="wrap hero">
<div class="hero-heading">
<p class="hero-eyebrow">恩平冯氏宗亲 · 数字族谱档案</p>
<h1>寻根有据，世系有源。</h1>
<p class="hero-intro">从一页家谱，读懂一家人的来处。留存珍贵原谱，让宗亲记忆代代相传。</p>
</div>
{indexed_search(homepage_index, home=True)}
<div class="home-quick-links">
<a href="/reader.html?p=1">从第一页开始</a>
<a href="/toc.html">查看全书目录</a>
</div></div>
<div class="wrap">
<section class="block"><h2>三大宗系</h2><div class="cards">{zu_cards}</div></section>
<section class="block"><h2>全书四章</h2><div class="cards">
<a class="card" href="/reader.html?p=44"><div class="big">第一章</div><div class="small">源流及现状</div></a>
<a class="card" href="/toc.html"><div class="big">第二章</div><div class="small">世系（全书主体）</div></a>
<a class="card" href="/reader.html?p=1101"><div class="big">第三章</div><div class="small">人物业绩</div></a>
<a class="card" href="/reader.html?p=1247"><div class="big">第四章</div><div class="small">文献、文物</div></a>
</div></section>
<section class="block"><h2>这本书</h2><div class="kv">
<div>查找恩平族谱、恩平宗谱或恩平家谱的宗亲，可在下方了解原书版本，再按村名、房支或原书页码找谱。</div>
<div>《恩平冯氏族谱》，恩平冯氏族谱重修筹委会编，1995 年付梓。全书四章，正文 1,269 页：源流、世系、人物业绩、文献文物。</div>
<div>世系章收复春、宁邦、万辅三大宗系及各房支系，分布于恩平各镇村。本站按原书顺序逐页呈现，可按目录、房支、村庄查找，也可直接输入书页码翻到那一页。</div>
</div></section>
<section class="block"><h2>找自己在哪一房</h2><div class="kv">
<div>先在家里的老谱、祠堂或长辈口中问清：属于哪个镇、哪个村、哪一房。再用上方搜索框输入村名或房名，找到对应支系，从支系第一页往下翻，就能顺着世系图找到自己这一支。</div>
</div></section>
</div>'''
    w('index.html', page('恩平冯氏族谱（1995 年重修版）｜在线查阅', body,
                         '在线查阅《恩平冯氏族谱》1995 年重修版，按目录、房支、村庄或书页码找谱。', 'home', url='/'))

    # ---------- toc ----------
    def target_of(e):
        if e.get('pdf'):
            return e['pdf'], label_for_pdf(e['pdf'])
        if e.get('p'):
            scan = NUMERIC_LOOKUP[e['p']]
            return scan, label_for_pdf(scan)
        return None
    raw_targets = [target_of(e) for e in all_entries]
    nexts = [None] * len(all_entries)
    nt = None
    for i in range(len(all_entries) - 1, -1, -1):
        nexts[i] = nt
        if raw_targets[i]:
            nt = raw_targets[i]
    rows = []
    prev_t = None
    for i, e in enumerate(all_entries):
        lvl = e.get('lvl', 3)
        t = raw_targets[i]
        if t is None:
            t = nexts[i] if lvl <= 1 else prev_t
        if raw_targets[i]:
            prev_t = raw_targets[i]
        href, lab = t
        # Imported levels also mark subtopics. Style only chapter and section labels as headings.
        title = e['t'].strip()
        heading = re.match(r'^第[一二三四五六七八九十百零〇0-9]+[章节]', title) or re.fullmatch(r'附篇[：:]?', title)
        css = ' class="grp"' if heading else ''
        related = branch_villages.get(e.get('id'), [])
        if not related:
            related = [name for name in village_aliases if name in title]
        key = esc(' '.join([title, lab, *related, alias_keys(related)]))
        rows.append(entry(reader_url(href), e['t'], lab, f'{css} data-q="{key}"'))
    body = f'''<div class="wrap"><section class="block"><h1>全书目录</h1>
<p><a class="btn" href="/villages.html">查看村庄 ›</a></p>
<p class="note">依原书目录逐条录入。点任意一条，直接翻到原书那一页。</p>
{indexed_search(homepage_index, toc=True)}
<div class="list" id="toclist">{"".join(rows)}</div></section></div>'''
    w('toc.html', page('全书目录｜恩平冯氏族谱', body, '查看《恩平冯氏族谱》全书目录，按章节和房支直达原书页。', 'toc', url='/toc.html'))

    # ---------- branch pages ----------
    for i, b in enumerate(branches):
        prev_b = branches[i - 1] if i > 0 else None
        next_b = branches[i + 1] if i + 1 < len(branches) else None
        page_links = ''.join(
            entry(reader_url(NUMERIC_LOOKUP[p]), label_for_pdf(NUMERIC_LOOKUP[p]), '看图')
            for p in range(b['p'], (b.get('end') or b['p']) + 1))
        nav = '<div class="btnrow">'
        if prev_b:
            nav += f'<a class="btn ghost" href="/branch/{prev_b["id"]}.html">← 上一支系</a>'
        if next_b:
            nav += f'<a class="btn ghost" href="/branch/{next_b["id"]}.html">下一支系 →</a>'
        nav += '</div>'
        body = f'''<div class="wrap"><nav class="crumb" aria-label="面包屑"><a href="/">恩平</a> / <a href="/toc.html">全书目录</a> / <span aria-current="page">{esc(b['t'])}</span></nav><section class="block"><h1>{esc(b['t'])}</h1>
<div class="kv">
<div><span class="k">所属宗系</span>{esc(b.get('zu',''))}</div>
<div><span class="k">所属房</span>{esc(b.get('fang',''))}</div>
<div><span class="k">原书页码</span>书第{b['p']}页{(' 至第' + str(b['end']) + '页') if b.get('end') and b['end'] != b['p'] else ''}</div>
{('<div><span class="k">涉及村庄</span>' + '、'.join('<a href="/villages.html#' + esc(v) + '">' + esc(v) + '</a>' for v in branch_villages.get(b['id'], [])) + '</div>') if branch_villages.get(b['id']) else ''}
</div>
<div class="btnrow"><a class="btn" href="{reader_url(NUMERIC_LOOKUP[b['p']])}">从本支系第一页看起</a></div>
<h2 style="font-size:17px">本支系各页</h2><div class="list">{page_links}</div>
{nav}</section></div>'''
        branch_path = f'/branch/{b["id"]}.html'
        desc = f'查阅《恩平冯氏族谱》1995 年重修版所载{b["t"]}，从原书第 {b["p"]} 页看起。'
        w(branch_path.lstrip('/'), page(f'{b["t"]}｜恩平冯氏族谱', body, desc, 'toc', url=branch_path))

    # ---------- villages ----------
    secs = []
    for v, bs in villages.items():
        links = ''.join(
            entry(f'/branch/{b["id"]}.html', b['t'], f'书第{b["p"]}页')
            for b in bs)
        q = v + ' ' + ' '.join(b['t'] for b in bs)
        q += ' ' + alias_keys([v])
        fresh = ''.join(
            f' <a class="fresh" href="{edition_path(e)}">{esc(edition_title(e))}</a>'
            for e in updates_by_book_village.get(v, []))
        q += ' ' + ' '.join(edition_title(e) for e in updates_by_book_village.get(v, []))
        secs.append(f'<div class="vsec" data-q="{esc(q)}"><div class="grp" id="{esc(v)}">{esc(v)}（{len(bs)} 个支系）{fresh}</div>{links}</div>')
    body = f'''<div class="wrap"><section class="block"><h1>村庄索引</h1>
<p><a class="btn" href="/toc.html">查看目录 ›</a></p>
<p class="note">按原书世系目录标题中出现的村名整理：同一个村可能有多个房支，同一房支也可能分布在多个村。点村名看该村涉及的支系。</p>
{search_box('vq', '输入村名或支系名', 'vcount')}
<div class="list">{"".join(secs)}</div></section></div>
<script>
filterList('vq', 'vcount', '.vsec', '个村');
</script>'''
    w('villages.html', page('村庄索引｜恩平冯氏族谱', body, '按村名查找原书收录的房支，查看对应谱页。', 'toc', url='/villages.html'))

    # ---------- buy ----------
    body = '''<div class="wrap"><section class="block"><h1>购买《恩平冯氏族谱》</h1>
<div class="kv">
<div>本站供宗亲免费在线查阅全书图片。</div>
<div>如需购买全书电子版（PDF 全本），请发邮件联系。</div>
<div style="font-size:22px;color:#742f32;font-weight:700;margin:10px 0"><a href="mailto:323748@gmail.com" style="color:inherit">点击购买</a></div>
<div>邮件主题可填写「购买恩平冯氏族谱」。</div>
</div></section></div>'''
    w('buy.html', page('购买联系｜恩平冯氏族谱', body, '《恩平冯氏族谱》全书电子版的购买联系信息。', 'buy', url='/buy.html'))

    # ---------- reader ----------
    branch_js = [{
        'id': b['id'], 't': b['t'], 'from': NUMERIC_LOOKUP[b['p']],
        'to': NUMERIC_LOOKUP[b.get('end') or b['p']],
    } for b in branches]
    reader_data = json.dumps({
        'pages': PAGES, 'numeric': NUMERIC_LOOKUP, 'branches': branch_js, 'start': NUMERIC_LOOKUP[1],
    }, ensure_ascii=False, separators=(',', ':')).replace('<', r'\u003c')
    sections = ''.join(f'<a href="{reader_url(scan)}">{esc(name)}</a>' for name, scan in SECTION_LINKS)
    body = f'''
<div class="wrap">
<nav class="edition-sheet-nav" aria-label="原书分区">{sections}</nav>
{reader_toolbar('/toc.html', '返回目录', BOOK_MAX, page_label='原书页码')}
<div class="readerwrap">
<button id="singlePage" class="reader-image" type="button" aria-label="放大当前谱页"><img class="pageimg" id="pg" alt="族谱原书页"></button>
<div id="scrollView" style="display:none"></div>
<div class="pagenav"><a id="prev" href="#">← 上一页</a><a id="next" href="#">下一页 →</a></div>
</div>
</div>
{image_dialog(edition=False)}
<script id="originalReaderData" type="application/json">{reader_data}</script>
<script src="/assets/reader-controls.js?v=1" defer></script>
<script src="/assets/original-reader.js?v=1" defer></script>'''
    w('reader.html', page('看原书｜恩平冯氏族谱', body, '逐页阅读《恩平冯氏族谱》1995 年重修版原书影像。', 'toc', url='/reader.html', index=False))

    # ---------- about ----------
    about = f'''<div class="wrap">
<section class="block about-content">
<h1>关于本站</h1>
<p>恩平冯氏族谱在线查阅站方便宗亲从村名、房支或书页码找谱。查找恩平族谱、恩平宗谱或恩平家谱时，可先核对自己要找的村名和房支，再选择原书或村庄更新资料。</p>
<h2>1995 年重修版从哪里来</h2>
<p>本站的全书目录、房支、村庄记录和原书影像，以《恩平冯氏族谱》1995 年重修版为底本。按原谱序记载，恩平冯氏修谱筹备委员会于 1992 年成立，组织编纂小组开展修谱工作，历时近三年，于 1995 年脱稿付梓。<a href="/reader.html?p=4">查看原谱卷首第 4 页</a>。</p>
<p>原书正文共 1,269 页，分为源流及现状、世系、人物业绩和文献文物四章。世系章载有复春系、宁邦房、万辅祖等宗系及下辖房支。</p>
<h2>怎样找 1995 年原书</h2>
<ul>
<li><strong>知道村名。</strong>打开<a href="/villages.html">村庄索引</a>，查该村在原书中涉及的房支，再打开对应谱页。同一个村可能对应多个房支。</li>
<li><strong>知道房支或章节。</strong>打开<a href="/toc.html">全书目录</a>，选择要找的章节或房支，按原书顺序查阅。</li>
<li><strong>知道原书页码。</strong>在<a href="/">首页搜索框</a>输入纸本页码，再从结果中选择原书或相应的新谱。</li>
</ul>
<h2>怎样查村庄更新资料</h2>
<p>各村后续增修的族谱按村庄、房支和年份整理，在<a href="{INDEX}">村庄更新资料</a>集中查阅。小湴村凝斋房 2026 版是这一房的更新资料，原书中的小湴村和凝斋房记录也可照常查阅。</p>
<p>打开<a href="{INDEX}v000100/">小湴村更新资料</a>，进入凝斋房 2026 版，输入姓名或人物编号。遇到同名人物时，可先核对世次，再从人物页查看祖先、后代关系与对应谱页。需要对照原谱照片时，可在档案页底部进入「原谱档案」，里面也列有已公开的修改记录。</p>
<h2>怎样反馈更正或补充资料</h2>
<p>请注明村名、房支和版本，附原书页码或新版谱页编号。若涉及人物，最好加上人物编号、建议更正的内容和相关出处。照片或其他资料请说明来源和可公开的范围。联系渠道见<a href="https://fengshizupu.com/about/">冯氏族谱主站的「关于」页</a>。</p>
<h2>资料撤下</h2>
<p>如认为站内某项资料涉及您的权益，或内容不应公开，请通过同一邮箱联系，注明页面网址和具体条目，核实后及时处理并回复。</p>
</section></div>'''
    w('about/index.html', page('关于本站｜恩平冯氏族谱', about,
                              '了解恩平冯氏族谱在线查阅站、1995 年重修版的来源、村庄更新资料及更正方式。', url='/about/'))

    # ---------- 404 ----------
    w('404.html', page('没有这一页', '<div class="wrap"><section class="block"><h2>没有这一页</h2><p>回到<a href="/">恩平首页</a>重新查找。</p></section></div>', '返回恩平冯氏族谱首页重新查找。', index=False))

    # ---------- sitemap ----------
    urls = ['/', '/toc.html', '/villages.html', '/buy.html', '/about/'] + [f'/branch/{b["id"]}.html' for b in branches] + edition_urls
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
         ''.join(f'<url><loc>{esc(ORIGIN + u)}</loc></url>\n' for u in urls) + '</urlset>'
    with open(os.path.join(SITE, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sm)
    with open(os.path.join(SITE, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write(f'User-agent: *\nAllow: /\nSitemap: {ORIGIN}/sitemap.xml\n')
    print('generated:', len(urls), 'urls,', len(branches), 'branches,', len(villages), 'villages')

def w(name, content):
    path = os.path.join(SITE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    build(load_data())
