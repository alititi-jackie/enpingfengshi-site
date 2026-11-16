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
from village_editions import INDEX, build_editions, edition_path, edition_title

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
TOTAL_PDF = 1301
BOOK_OFFSET = 30          # book page N = PDF page N+30
BOOK_MAX = 1269

RED = '#742f32'

def esc(s):
    return html.escape(str(s), quote=True)

def label_for_pdf(n):
    if n <= 17:
        return f'卷首第{n}页'
    if n <= 30:
        return f'目录第{n-17}页'
    if n <= 43:
        return f'目录第{n-30}页'
    if n <= BOOK_MAX + BOOK_OFFSET:
        return f'书第{n-BOOK_OFFSET}页'
    return '封底'

def reader_url(pdf_page):
    return f'/reader.html?p={pdf_page}'

def search_box(field, hint, count=None):
    status = f'<div class="vcount" id="{count}" role="status"></div>' if count else ''
    button = '' if count else '<button id="go" type="button">搜索</button>'
    return f'<div class="searchbox"><input id="{field}" type="text" placeholder="{esc(hint)}" aria-label="{esc(hint)}" autocomplete="off">{button}</div>{status}'

def entry(href, title, detail, attributes=''):
    return f'<a{attributes} href="{esc(href)}"><span>{esc(title)}</span><span class="pg">{esc(detail)}</span></a>'

ORIGIN = 'https://enping.fengshizupu.com'


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
<link rel="stylesheet" href="/assets/style.css">
<script src="/assets/site.js"></script>
</head>
<body>'''

def header(active=''):
    links = [('首页', '/', 'home'), ('目录', '/toc.html', 'toc'), ('村庄', '/villages.html', 'villages'),
             ('村庄更新资料', INDEX, 'editions'), ('购买', '/buy.html', 'buy'), ('主站', 'https://fengshizupu.com', 'main')]
    parts = []
    for t, u, k in links:
        cls = ' class="on"' if k == active else ''
        parts.append(f'<a href="{u}"{cls}>{t}</a>')
    nav = ''.join(parts) + '<button class="share" type="button" onclick="sharePage()">分享</button>'
    return f'''<header class="brandbar"><div class="wrap">
<a class="brand" href="/"><img src="/assets/icon.svg" alt="冯" width="46" height="46"><span>恩平冯氏族谱<small>enping.fengshizupu.com</small></span></a>
</div></header>
<nav class="mainnav"><div class="wrap mainnav-in">{nav}</div></nav>'''

FOOT = '''<footer class="site">恩平冯氏族谱 · 在线查阅<br>
<strong>本站原书版本 ·《恩平冯氏族谱》1995 年重修版</strong><br>
全国数字族谱平台 · <a href="https://fengshizupu.com/">fengshizupu.com</a> · <a href="/about/">关于本站</a>
</footer>
</body></html>'''

FAB = '''<div class="fab"><button id="fabTop" type="button" title="回到顶部" aria-label="回到顶部">↑</button><button id="fabBack" type="button" title="返回" aria-label="返回" onclick="history.back()">←</button></div>
<script>
var ft = document.getElementById('fabTop');
function fabShow(){ ft.classList.toggle('on', window.scrollY > 900); }
window.addEventListener('scroll', fabShow, {passive: true}); fabShow();
ft.onclick = function(){ window.scrollTo({top: 0, behavior: 'smooth'}); };
function sharePage(){ var u = location.href, t = document.title;
  var description = document.querySelector('meta[name="description"]').content;
  if (navigator.share) { navigator.share({title: t, text: description, url: u}).catch(function(){}); }
  else if (navigator.clipboard) { navigator.clipboard.writeText(u).then(function(){ alert('链接已复制'); }); } }
</script>'''

def page(title, body, desc, active='', *, url=None, index=True):
    return head(title, desc, url, index) + header(active) + body + FAB + FOOT


def load_data():
    with open(os.path.join(ROOT, 'data', 'toc.json'), encoding='utf-8') as f:
        return json.load(f)

def extract_villages(branches):
    """Pull town/village names out of branch titles."""
    vmap = {}
    pat = re.compile(r'([一-龥]{2,4}镇)?([一-龥]{2,5}村)')
    for b in branches:
        found = set()
        for m in pat.finditer(b['t']):
            name = (m.group(1) or '') + m.group(2)
            if len(m.group(2)) >= 2 and m.group(2) not in ('本村',):
                found.add(name)
        for v in found:
            vmap.setdefault(v, []).append(b)
    return dict(sorted(vmap.items(), key=lambda kv: -len(kv[1])))

def build(data):
    os.makedirs(SITE, exist_ok=True)
    os.makedirs(os.path.join(SITE, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(SITE, 'branch'), exist_ok=True)
    shutil.copy(os.path.join(ROOT, 'assets', 'site.js'), os.path.join(SITE, 'assets', 'site.js'))
    shutil.copy(os.path.join(ROOT, 'assets', 'style.css'), os.path.join(SITE, 'assets', 'style.css'))
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
    edition_results, edition_urls, updated_villages = build_editions(
        ROOT, SITE, page, w, entry, search_box, villages)
    updates_by_book_village = {}
    for editions in updated_villages.values():
        for edition in editions:
            updates_by_book_village.setdefault(edition.get('bookVillage'), []).append(edition)
    branch_villages = {}
    for name, bs in villages.items():
        for b in bs:
            branch_villages.setdefault(b['id'], []).append(name)

    # ---------- index ----------
    search_data = []
    for e in all_entries:
        if e.get('p'):
            search_data.append({'t': e['t'], 'p': e['p'], 'kind': 'toc'})
        elif e.get('pdf'):
            search_data.append({'t': e['t'], 'pdf': e['pdf'], 'kind': 'toc'})
    for b in branches:
        vs = branch_villages.get(b['id'], [])
        kw = ' '.join(vs)
        if any('小湴' in v for v in vs):
            kw += ' 小滘 小滘村'
        search_data.append({'t': b['t'], 'p': b['p'], 'kind': 'branch', 'id': b['id'],
                            'zu': b.get('zu', ''), 'fang': b.get('fang', ''), 'k': kw})
    for v, bs in villages.items():
        kw = '小滘 小滘村' if '小湴' in v else ''
        search_data.append({'t': v, 'p': bs[0]['p'], 'kind': 'village', 'k': kw})
    zu_cards = ''
    for zu, desc in [('复春系', '九房 · 书第32–890页'), ('宁邦房', '一至二十世 · 书第891–977页'),
                     ('万辅祖', '一至十六世 · 书第978–1070页')]:
        first = next((b for b in branches if b.get('zu', '').startswith(zu[:2])), None)
        href = f"/branch/{first['id']}.html" if first else '/toc.html'
        zu_cards += f'<a class="card" href="{href}"><div class="big">{zu}</div><div class="small">{desc}</div></a>'
    body = f'''
<div class="hero">
<h1>寻根溯源 · 世系传承</h1>
{search_box('q', '输入村名、房支、书页码或新版人名')}<div id="searchResults" role="status"></div>
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
<div>《恩平冯氏族谱》，恩平冯氏族谱重修筹委会编，1995 年付梓。全书四章，正文 1,269 页：源流、世系、人物业绩、文献文物。</div>
<div>世系章收复春、宁邦、万辅三大宗系及各房支系，分布于恩平各镇村。本站按原书顺序逐页呈现，可按目录、房支、村庄查找，也可直接输入书页码翻到那一页。</div>
</div></section>
<section class="block"><h2>找自己在哪一房</h2><div class="kv">
<div>先在家里的老谱、祠堂或长辈口中问清：属于哪个镇、哪个村、哪一房。再用上方搜索框输入村名或房名，找到对应支系，从支系第一页往下翻，就能顺着世系图找到自己这一支。</div>
</div></section>
</div>
<script>
const DATA = {json.dumps(search_data, ensure_ascii=False)};
const EDITIONS = {json.dumps(edition_results, ensure_ascii=False).replace('<', chr(92) + 'u003c')};
const q = document.getElementById('q'), box = document.getElementById('searchResults');
function run(){{
  const s = normalizeQuery(q.value); box.innerHTML = '';
  if(!s) return;
  if(/^\\d+$/.test(s)){{ const bp = parseInt(s);
    if(bp>=1 && bp<={BOOK_MAX}){{ box.innerHTML = '<a href="' + readerURL(bp + {BOOK_OFFSET}) + '">打开原书第 ' + bp + ' 页<span class="pg">书页直达 · 点这里翻过去</span></a>'; }}
    else {{ box.innerHTML = '<a>书页码在 1–' + {BOOK_MAX} + ' 之间</a>'; }}
    return; }}
  const hits = DATA.filter(d => normalizeQuery(d.t + ' ' + (d.k || '')).includes(s)).slice(0, 12);
  const editionHits = EDITIONS.filter(d => d.kind === 'edition' &&
    normalizeQuery(d.t + ' ' + d.k).includes(s));
  const people = EDITIONS.filter(d => d.kind === 'person' &&
    normalizeQuery(d.t + ' ' + d.k).includes(s)).sort((a, b) =>
      Number(normalizeQuery(b.t) === s) - Number(normalizeQuery(a.t) === s)).slice(0, 12);
  if(!hits.length && !editionHits.length && !people.length){{ box.innerHTML = '<a>暂未找到相关记录，请换个关键词或查看全书目录</a>'; return; }}
  box.innerHTML = '<p>显示 ' + (hits.length + editionHits.length + people.length) + ' 条相关记录</p>' + hits.map(d => {{
    const href = d.kind === 'branch' ? '/branch/' + d.id + '.html' :
                 d.kind === 'village' ? '/villages.html#' + encodeURIComponent(d.a || d.t) :
                 d.pdf ? readerURL(d.pdf) : readerURL(d.p + {BOOK_OFFSET});
    const tag = d.kind === 'branch' ? (d.zu + ' ' + d.fang) : (d.kind === 'village' ? '村庄' : '目录');
    const pg = d.pdf ? '卷首' : '书第' + d.p + '页';
    return '<a href="' + href + '">' + d.t + '<span class="pg">' + tag + ' · ' + pg + '</span></a>';
  }}).join('');
  function appendEditionResult(d, before) {{
    const link = document.createElement('a');
    link.href = d.url;
    link.className = 'edition-result';
    link.textContent = d.t;
    const detail = document.createElement('span');
    detail.className = 'pg';
    detail.textContent = d.detail;
    link.append(detail);
    box.insertBefore(link, before);
  }}
  const firstOriginal = box.querySelector('a');
  for (const edition of editionHits) appendEditionResult(edition, firstOriginal);
  for (const person of people) appendEditionResult(person, null);
}}
function jumpNum(){{ const s = normalizeQuery(q.value);
  if(/^\\d+$/.test(s)){{ const bp = parseInt(s); if(bp>=1 && bp<={BOOK_MAX}){{ location.href = readerURL(bp + {BOOK_OFFSET}); return true; }} }}
  return false; }}
document.getElementById('go').onclick = () => {{ if(!jumpNum()) run(); }};
q.addEventListener('input', run);
q.addEventListener('keydown', e => {{ if(e.key === 'Enter' && !jumpNum()) run(); }});
const incomingQuery = new URLSearchParams(window.location.search).get('q');
if (incomingQuery !== null && incomingQuery.trim() !== '') {{
  q.value = incomingQuery.trim();
  if (!jumpNum()) run();
}}
</script>'''
    w('index.html', page('恩平冯氏族谱 · 1995 年重修版', body,
                         '在线查阅《恩平冯氏族谱》1995 年重修版，按目录、房支、村庄或书页码找谱。', 'home', url='/'))

    # ---------- toc ----------
    def target_of(e):
        if e.get('pdf'):
            return e['pdf'], label_for_pdf(e['pdf'])
        if e.get('p'):
            return e['p'] + BOOK_OFFSET, f'书第{e["p"]}页'
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
        css = ' class="grp"' if lvl <= 1 else ' class="note-link"' if not raw_targets[i] else ''
        key = esc(e['t'] + ' ' + lab + (f' {e["p"]}' if e.get('p') else ''))
        rows.append(entry(reader_url(href), e['t'], lab, f'{css} data-q="{key}"'))
    body = f'''<div class="wrap"><section class="block"><h2>全书目录</h2>
<p class="note">依原书目录逐条录入。点任意一条，直接翻到原书那一页。</p>
{search_box('tq', '输入条目、村名或书页码', 'tcount')}
<div class="list" id="toclist">{"".join(rows)}</div></section></div>
<script>
filterList('tq', 'tcount', '#toclist > a', '条');
</script>'''
    w('toc.html', page('全书目录｜恩平冯氏族谱', body, '查看《恩平冯氏族谱》全书目录，按章节和房支直达原书页。', 'toc', url='/toc.html'))

    # ---------- branch pages ----------
    for i, b in enumerate(branches):
        prev_b = branches[i - 1] if i > 0 else None
        next_b = branches[i + 1] if i + 1 < len(branches) else None
        page_links = ''.join(
            entry(reader_url(p + BOOK_OFFSET), f'书第{p}页', '看图')
            for p in range(b['p'], (b.get('end') or b['p']) + 1))
        nav = '<div class="btnrow">'
        if prev_b:
            nav += f'<a class="btn ghost" href="/branch/{prev_b["id"]}.html">← 上一支系</a>'
        if next_b:
            nav += f'<a class="btn ghost" href="/branch/{next_b["id"]}.html">下一支系 →</a>'
        nav += '</div>'
        body = f'''<div class="wrap"><nav class="crumb" aria-label="面包屑"><a href="/">首页</a> / <a href="/toc.html">全书目录</a> / <span aria-current="page">{esc(b['t'])}</span></nav><section class="block"><h2>{esc(b['t'])}</h2>
<div class="kv">
<div><span class="k">所属宗系</span>{esc(b.get('zu',''))}</div>
<div><span class="k">所属房</span>{esc(b.get('fang',''))}</div>
<div><span class="k">原书页码</span>书第{b['p']}页{(' 至第' + str(b['end']) + '页') if b.get('end') and b['end'] != b['p'] else ''}</div>
{('<div><span class="k">涉及村庄</span>' + '、'.join('<a href="/villages.html#' + esc(v) + '">' + esc(v) + '</a>' for v in branch_villages.get(b['id'], [])) + '</div>') if branch_villages.get(b['id']) else ''}
</div>
<div class="btnrow"><a class="btn" href="{reader_url(b['p'] + BOOK_OFFSET)}">从本支系第一页看起</a></div>
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
        if '小湴' in v:
            q += ' 小滘 小滘村'
        fresh = ''.join(
            f' <a class="fresh" href="{edition_path(e)}">{esc(edition_title(e))}</a>'
            for e in updates_by_book_village.get(v, []))
        q += ' ' + ' '.join(edition_title(e) for e in updates_by_book_village.get(v, []))
        secs.append(f'<div class="vsec" data-q="{esc(q)}"><div class="grp" id="{esc(v)}">{esc(v)}（{len(bs)} 个支系）{fresh}</div>{links}</div>')
    body = f'''<div class="wrap"><section class="block"><h2>村庄索引</h2>
<p class="note">按原书世系目录标题中出现的村名整理：同一个村可能有多个房支，同一房支也可能分布在多个村。点村名看该村涉及的支系。</p>
{search_box('vq', '输入村名或支系名', 'vcount')}
<div class="list">{"".join(secs)}</div></section></div>
<script>
filterList('vq', 'vcount', '.vsec', '个村');
</script>'''
    w('villages.html', page('村庄索引｜恩平冯氏族谱', body, '按村名查找原书收录的房支，查看对应谱页。', 'villages', url='/villages.html'))

    # ---------- buy ----------
    body = '''<div class="wrap"><section class="block"><h2>购买《恩平冯氏族谱》</h2>
<div class="kv">
<div>本站供宗亲免费在线查阅全书图片。</div>
<div>如需购买全书电子版（PDF 全本），请加微信联系：</div>
<div style="font-size:22px;color:#742f32;font-weight:700;margin:10px 0">微信：hola24</div>
<div>加微信时请注明来意（例如：购买恩平冯氏族谱），以便通过。</div>
</div></section></div>'''
    w('buy.html', page('购买联系｜恩平冯氏族谱', body, '《恩平冯氏族谱》全书电子版的购买联系信息。', 'buy', url='/buy.html'))

    # ---------- reader ----------
    branch_js = [{'id': b['id'], 't': b['t'], 'zu': b.get('zu', ''), 'fang': b.get('fang', ''),
                  'from': b['p'] + BOOK_OFFSET, 'to': (b.get('end') or b['p']) + BOOK_OFFSET}
                 for b in branches]
    body = f'''
<div class="readerbar">
<a class="nav" href="/toc.html">返回目录</a>
<span class="info" id="info"></span>
<span class="info" id="branchInfo"></span>
<span style="flex:1"></span>
<span class="modes"><button id="mSingle" type="button">单页</button><button id="mScroll" type="button">连看</button></span>
<button id="jumpToggle" type="button">跳页</button>
<label class="info jumpctl">书页 <input id="jump" type="number" min="1" max="{BOOK_MAX}"></label>
<button class="primary" id="jumpBtn">跳页</button>
</div>
<div class="readerwrap">
<button id="singlePage" class="reader-image" type="button" aria-label="放大当前谱页"><img class="pageimg" id="pg" alt="族谱原书页"></button>
<div id="scrollView" style="display:none"></div>
<div class="pagenav"><a id="prev" href="#">← 上一页</a><a id="next" href="#">下一页 →</a></div>
</div>
<dialog id="imageDialog" class="image-dialog" aria-labelledby="imageLabel">
<div class="image-toolbar"><span id="imageLabel"></span><button type="button" id="imageZoom">放大查看</button><button type="button" id="imageClose">关闭</button></div>
<div class="image-viewport"><img id="imageLarge" alt=""></div>
</dialog>
<script>
if('scrollRestoration' in history) history.scrollRestoration = 'manual';
const TOTAL = {TOTAL_PDF}, OFF = {BOOK_OFFSET}, BMAX = {BOOK_MAX};
const BR = {json.dumps(branch_js, ensure_ascii=False)};
const PAGE_LABELS = {json.dumps([''] + [label_for_pdf(n) for n in range(1, TOTAL_PDF + 1)], ensure_ascii=False)};
function label(n){{ return PAGE_LABELS[n]; }}
let p = parseInt(new URLSearchParams(location.search).get('p') || '31');
if(!(p>=1 && p<=TOTAL)) p = 31;
const img = document.getElementById('pg');
const sv = document.getElementById('scrollView');
function src(n){{ return '/pages/p' + String(n).padStart(4,'0') + '.webp'; }}
function infoFor(n){{
  document.getElementById('info').innerHTML = '<b>' + label(n) + '</b><span class="full-only">（全书图第' + n + '页）</span>';
  const bs = BR.filter(x => n>=x.from && n<=x.to);
  document.getElementById('branchInfo').innerHTML = bs.length ?
    '所属支系：' + bs.map(x => '<a href="/branch/' + x.id + '.html"><b>' + x.t + '</b></a>').join('、') : '';
  const pv = document.getElementById('prev'), nx = document.getElementById('next');
  pv.className = n<=1 ? 'off' : ''; nx.className = n>=TOTAL ? 'off' : '';
}}
function render(){{
  img.src = src(p);
  img.alt = '《恩平冯氏族谱》' + label(p);
  infoFor(p);
  window.scrollTo(0,0);
}}
function sync(){{ history.replaceState(null,'','?p='+p); render(); }}
let mode = 'scroll';
try{{ mode = localStorage.getItem('readerMode') || 'scroll'; }}catch(e){{}}
if(mode !== 'scroll') mode = 'single';
let lo = 0, hi = 0;
const WIN = 7;
function blockHTML(n){{
  const bs = BR.filter(x => n>=x.from && n<=x.to);
  const bt = bs.length ? ' · ' + bs.map(x => x.t).join('、') : '';
  return '<div class="spage" data-p="' + n + '"><div class="scap"><b>' + label(n) + '</b>（全书图第' + n + '页）' + bt + '</div>' +
    '<button class="reader-image" type="button" aria-label="放大' + label(n) + '"><img class="pageimg" loading="lazy" src="' + src(n) + '" alt="《恩平冯氏族谱》' + label(n) + '"></button></div>';
}}
function blockEl(n){{ return sv.querySelector('.spage[data-p="' + n + '"]'); }}
function buildScroll(center){{
  lo = Math.max(1, center - WIN); hi = Math.min(TOTAL, center + WIN);
  let h = ''; for(let n = lo; n <= hi; n++) h += blockHTML(n);
  sv.innerHTML = h;
}}
function barOffset(){{
  const nav = document.querySelector('.mainnav');
  const bar = document.querySelector('.readerbar');
  return (nav ? nav.offsetHeight : 48) + (bar ? bar.offsetHeight : 50) + 6;
}}
let holdUntil = 0;
function scrollToPage(n, smooth){{
  const el = blockEl(n); if(!el) return;
  const y = el.getBoundingClientRect().top + window.scrollY - barOffset();
  holdUntil = Date.now() + 180;
  window.scrollTo({{ top: y, behavior: smooth ? 'smooth' : 'auto' }});
}}
function anchorTop(){{
  const els = sv.querySelectorAll('.spage');
  for(let i = 0; i < els.length; i++){{
    const r = els[i].getBoundingClientRect();
    if(r.bottom > 0) return {{ n: parseInt(els[i].dataset.p), top: r.top }};
  }}
  return null;
}}
function restoreAnchor(a){{
  if(!a) return;
  const el = blockEl(a.n);
  if(el) window.scrollBy(0, el.getBoundingClientRect().top - a.top);
}}
function currentFromScroll(){{
  const line = barOffset() + 30;
  let cur = lo, best = 0;
  const els = sv.querySelectorAll('.spage');
  for(let i = 0; i < els.length; i++){{
    const r = els[i].getBoundingClientRect();
    if(r.top <= line) cur = parseInt(els[i].dataset.p);
    if(r.top <= line && r.bottom > line){{ best = parseInt(els[i].dataset.p); break; }}
  }}
  return best || cur;
}}
let ticking = false;
function onScroll(){{
  if(mode !== 'scroll' || ticking) return;
  ticking = true;
  requestAnimationFrame(() => {{
    ticking = false;
    if(mode !== 'scroll' || Date.now() < holdUntil) return;
    const cur = currentFromScroll();
    if(cur !== p){{ p = cur; history.replaceState(null,'','?p='+p); infoFor(p); }}
    if(hi < TOTAL && hi - p <= 3){{
      let h = ''; const nhi = Math.min(TOTAL, hi + WIN);
      for(let n = hi + 1; n <= nhi; n++) h += blockHTML(n);
      sv.insertAdjacentHTML('beforeend', h); hi = nhi;
    }}
    if(lo > 1 && p - lo <= 3){{
      let h = ''; const nlo = Math.max(1, lo - WIN);
      for(let n = nlo; n <= lo - 1; n++) h += blockHTML(n);
      const a = anchorTop();
      sv.insertAdjacentHTML('afterbegin', h);
      restoreAnchor(a);
      lo = nlo;
    }}
    if(hi - p > WIN + 10){{
      const n = p + WIN + 4;
      sv.querySelectorAll('.spage').forEach(el => {{ if(parseInt(el.dataset.p) > n) el.remove(); }});
      hi = n;
    }}
    if(p - lo > WIN + 10){{
      const n = p - WIN - 4;
      const a = anchorTop();
      sv.querySelectorAll('.spage').forEach(el => {{ if(parseInt(el.dataset.p) < n) el.remove(); }});
      restoreAnchor(a);
      lo = n;
    }}
  }});
}}
window.addEventListener('scroll', onScroll, {{ passive: true }});
function gotoPage(n, smooth){{
  p = Math.max(1, Math.min(TOTAL, n));
  history.replaceState(null,'','?p='+p);
  if(mode === 'scroll'){{
    if(p < lo || p > hi) buildScroll(p);
    infoFor(p);
    scrollToPage(p, !!smooth);
  }} else render();
}}
function setMode(m){{
  mode = m;
  try{{ localStorage.setItem('readerMode', m); }}catch(e){{}}
  document.getElementById('mSingle').className = m === 'single' ? 'on' : '';
  document.getElementById('mScroll').className = m === 'scroll' ? 'on' : '';
  document.body.classList.toggle('scrollmode', m === 'scroll');
  const single = m === 'single';
  document.getElementById('singlePage').style.display = single ? '' : 'none';
  sv.style.display = single ? 'none' : '';
  if(single) render();
  else {{ buildScroll(p); infoFor(p); scrollToPage(p, false);
    requestAnimationFrame(() => {{ if(mode === 'scroll') scrollToPage(p, false); }}); }}
}}
document.getElementById('mSingle').onclick = () => setMode('single');
document.getElementById('mScroll').onclick = () => setMode('scroll');
document.getElementById('prev').onclick = e => {{ e.preventDefault(); if(p>1){{ if(mode === 'scroll') gotoPage(p - 1, true); else {{ p--; sync(); }} }} }};
document.getElementById('next').onclick = e => {{ e.preventDefault(); if(p<TOTAL){{ if(mode === 'scroll') gotoPage(p + 1, true); else {{ p++; sync(); }} }} }};
document.getElementById('jumpToggle').onclick = () => document.body.classList.toggle('jumpon');
document.getElementById('jumpBtn').onclick = () => {{
  const v = parseInt(document.getElementById('jump').value);
  document.body.classList.remove('jumpon');
  if(v>=1 && v<=BMAX) gotoPage(v + OFF, false); }};
const imageDialog = bindImageDialog();
document.getElementById('singlePage').onclick = () => imageDialog.open(src(p), label(p));
sv.addEventListener('click', e => {{
  const button = e.target.closest('.reader-image');
  if (!button) return;
  const n = Number(button.closest('.spage').dataset.p);
  imageDialog.open(src(n), label(n));
}});
document.addEventListener('keydown', e => {{
  if(imageDialog.dialog.open) return;
  if(e.target && e.target.id === 'jump') return;
  if(e.key==='ArrowLeft' && p>1){{ if(mode === 'scroll') gotoPage(p - 1, true); else {{ p--; sync(); }} }}
  if(e.key==='ArrowRight' && p<TOTAL){{ if(mode === 'scroll') gotoPage(p + 1, true); else {{ p++; sync(); }} }} }});
setMode(mode);
</script>'''
    w('reader.html', page('看原书｜恩平冯氏族谱', body, '逐页阅读《恩平冯氏族谱》1995 年重修版原书影像。', 'toc', url='/reader.html', index=False))

    # ---------- about ----------
    about = f'''<div class="wrap">
<section class="block"><h1>关于本站</h1>
<p>恩平冯氏族谱在线查阅站供宗亲寻根查谱。可按<a href="/toc.html">目录和房支</a>、<a href="/villages.html">村庄</a>或书页码查找原书。</p>
<h2>原书版本</h2>
<p>本站的全书目录、房支、村庄记录和原书影像以《恩平冯氏族谱》1995 年重修版为底本。原谱序记载，此次修谱于 1992 年启动，1995 年脱稿付梓。<a href="/reader.html?p=4">查看原谱卷首第 4 页</a>。</p>
<h2>村庄更新资料</h2>
<p>小湴村凝斋房 2026 版是该房的更新资料，可查姓名、看世系和核对谱页。各村后续增修资料按村庄、房支和年份整理，见<a href="{INDEX}">村庄更新资料</a>。</p>
<h2>更正与补充</h2>
<p>如发现错漏或有资料补充，请注明村名、房支、版本、谱页和相关依据。联系渠道见<a href="https://fengshizupu.com/about/">冯氏族谱主站的「关于」页</a>。</p>
</section></div>'''
    w('about/index.html', page('关于本站｜恩平冯氏族谱', about,
                              '了解恩平冯氏族谱在线查阅站、1995 年重修版的来源、村庄更新资料及更正方式。', url='/about/'))

    # ---------- 404 ----------
    w('404.html', page('没有这一页', '<div class="wrap"><section class="block"><h2>没有这一页</h2><p>回到<a href="/">首页</a>重新查找。</p></section></div>', '返回恩平冯氏族谱首页重新查找。', index=False))

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
