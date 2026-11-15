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

def head(title, desc=''):
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>'''

def header(active=''):
    links = [('首页', '/', 'home'), ('目录', '/toc.html', 'toc'), ('村庄', '/villages.html', 'villages'),
             ('购买', '/buy.html', 'buy'), ('主站', 'https://fengshizupu.com', 'main')]
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
<span>本站内容依《恩平冯氏族谱》原书制作，供宗亲查阅。</span><br>
<a class="foot-main" href="https://fengshizupu.com" target="_blank" rel="noopener">fengshizupu.com</a></footer>
</body></html>'''

FAB = '''<div class="fab"><button id="fabTop" type="button" title="回到顶部" aria-label="回到顶部">↑</button><button id="fabBack" type="button" title="返回" aria-label="返回" onclick="history.back()">←</button></div>
<script>
var ft = document.getElementById('fabTop');
function fabShow(){ ft.classList.toggle('on', window.scrollY > 900); }
window.addEventListener('scroll', fabShow, {passive: true}); fabShow();
ft.onclick = function(){ window.scrollTo({top: 0, behavior: 'smooth'}); };
function sharePage(){ var u = location.href, t = document.title;
  if (navigator.share) { navigator.share({title: t, url: u}).catch(function(){}); }
  else if (navigator.clipboard) { navigator.clipboard.writeText(u).then(function(){ alert('链接已复制'); }); } }
</script>'''

def page(title, body, desc='', active=''):
    return head(title, desc) + header(active) + body + FAB + FOOT

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
    shutil.copy(os.path.join(ROOT, 'assets', 'style.css'), os.path.join(SITE, 'assets', 'style.css'))
    shutil.copy(os.path.join(ROOT, 'assets', 'icon.svg'), os.path.join(SITE, 'assets', 'icon.svg'))
    shutil.copy(os.path.join(ROOT, 'favicon.svg'), os.path.join(SITE, 'favicon.svg'))
    import glob
    for vf in glob.glob(os.path.join(ROOT, 'baidu_verify_*.html')):
        shutil.copy(vf, os.path.join(SITE, os.path.basename(vf)))

    branches = data['branches']
    all_entries = data['all']
    by_id = {b['id']: b for b in branches}
    villages = {name: [by_id[i] for i in ids] for name, ids in data.get('villages', {}).items()}
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
<h1>恩平冯氏族谱</h1><div class="sub">寻 根 溯 源 · 世 系 传 承</div>
<div class="searchbox"><input id="q" type="text" placeholder="输入房名、支系、村名，或书页码" autocomplete="off">
<button id="go">查 找</button></div><div id="searchResults"></div>
<div class="btnrow"><a class="btn" href="/reader.html?p=1">从第一页开始看</a>
<a class="btn ghost" href="/toc.html">看全书目录</a></div></div>
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
const q = document.getElementById('q'), box = document.getElementById('searchResults');
function run(){{
  const s = q.value.trim(); box.innerHTML = '';
  if(!s) return;
  if(/^\\d+$/.test(s)){{ const bp = parseInt(s);
    if(bp>=1 && bp<={BOOK_MAX}){{ box.innerHTML = '<a href="/reader.html?p=' + (bp + {BOOK_OFFSET}) + '">打开原书第 ' + bp + ' 页<span class="pg">书页直达 · 点这里翻过去</span></a>'; }}
    else {{ box.innerHTML = '<a>书页码在 1–' + {BOOK_MAX} + ' 之间</a>'; }}
    return; }}
  const hits = DATA.filter(d => (d.t + ' ' + (d.k || '')).includes(s)).slice(0, 12);
  if(!hits.length){{ box.innerHTML = '<a>没有找到，换个词试试，或去目录页翻找</a>'; return; }}
  box.innerHTML = hits.map(d => {{
    const href = d.kind === 'branch' ? '/branch/' + d.id + '.html' :
                 d.kind === 'village' ? '/villages.html#' + encodeURIComponent(d.a || d.t) :
                 d.pdf ? '/reader.html?p=' + d.pdf : '/reader.html?p=' + (d.p + {BOOK_OFFSET});
    const tag = d.kind === 'branch' ? (d.zu + ' ' + d.fang) : (d.kind === 'village' ? '村庄' : '目录');
    const pg = d.pdf ? '卷首' : '书第' + d.p + '页';
    return '<a href="' + href + '">' + d.t + '<span class="pg">' + tag + ' · ' + pg + '</span></a>';
  }}).join('');
}}
function jumpNum(){{ const s = q.value.trim();
  if(/^\\d+$/.test(s)){{ const bp = parseInt(s); if(bp>=1 && bp<={BOOK_MAX}){{ location.href = '/reader.html?p=' + (bp + {BOOK_OFFSET}); return true; }} }}
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
    w('index.html', page('恩平冯氏族谱｜在线查阅', body,
                         '《恩平冯氏族谱》在线查阅：按目录、房支、村庄查找，或输入书页码直接翻到原书那一页。', 'home'))

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
        q = esc(e['t'] + ' ' + lab)
        pg = f'<span class="pg">{lab}</span>'
        if lvl <= 1:
            rows.append(f'<a class="grp" data-q="{q}" href="/reader.html?p={href}"><span>{esc(e["t"])}</span>{pg}</a>')
        elif raw_targets[i]:
            rows.append(f'<a data-q="{q}" href="/reader.html?p={href}"><span>{esc(e["t"])}</span>{pg}</a>')
        else:
            rows.append(f'<a class="note-link" data-q="{q}" href="/reader.html?p={href}"><span>{esc(e["t"])}</span>{pg}</a>')
    body = f'''<div class="wrap"><section class="block"><h2>全书目录</h2>
<p class="note">依原书目录逐条录入。点任意一条，直接翻到原书那一页。</p>
<div class="vsearch"><input id="tq" type="text" placeholder="输入条目、村名或页码，如：凝斋、莲塘、192" autocomplete="off"><div class="vcount" id="tcount"></div></div>
<div class="list" id="toclist">{"".join(rows)}</div></section></div>
<script>
var tq = document.getElementById('tq'), tc = document.getElementById('tcount');
var trows = Array.prototype.slice.call(document.getElementById('toclist').children);
tq.addEventListener('input', function(){{
  var s = tq.value.trim(), n = 0;
  trows.forEach(function(x){{ var show = !s || x.getAttribute('data-q').indexOf(s) >= 0;
    x.style.display = show ? '' : 'none'; if (show) n++; }});
  tc.textContent = s ? ('找到 ' + n + ' 条') : '';
}});
</script>'''
    w('toc.html', page('全书目录｜恩平冯氏族谱', body, '', 'toc'))

    # ---------- branch pages ----------
    for i, b in enumerate(branches):
        prev_b = branches[i - 1] if i > 0 else None
        next_b = branches[i + 1] if i + 1 < len(branches) else None
        page_links = ''.join(
            f'<a href="/reader.html?p={p + BOOK_OFFSET}"><span>书第{p}页</span><span class="pg">看图</span></a>'
            for p in range(b['p'], (b.get('end') or b['p']) + 1))
        nav = '<div class="btnrow">'
        if prev_b:
            nav += f'<a class="btn ghost" href="/branch/{prev_b["id"]}.html">← 上一支系</a>'
        if next_b:
            nav += f'<a class="btn ghost" href="/branch/{next_b["id"]}.html">下一支系 →</a>'
        nav += '</div>'
        body = f'''<div class="wrap"><section class="block"><h2>{esc(b['t'])}</h2>
<div class="kv">
<div><span class="k">所属宗系</span>{esc(b.get('zu',''))}</div>
<div><span class="k">所属房</span>{esc(b.get('fang',''))}</div>
<div><span class="k">原书页码</span>书第{b['p']}页{(' 至第' + str(b['end']) + '页') if b.get('end') and b['end'] != b['p'] else ''}</div>
{('<div><span class="k">涉及村庄</span>' + '、'.join('<a href="/villages.html#' + esc(v) + '">' + esc(v) + '</a>' for v in branch_villages.get(b['id'], [])) + '</div>') if branch_villages.get(b['id']) else ''}
</div>
<div class="btnrow"><a class="btn" href="/reader.html?p={b['p'] + BOOK_OFFSET}">从本支系第一页看起</a></div>
<h2 style="font-size:17px">本支系各页</h2><div class="list">{page_links}</div>
{nav}</section></div>'''
        w(f'branch/{b["id"]}.html', page(f'{b["t"]}｜恩平冯氏族谱', body, '', 'toc'))

    # ---------- villages ----------
    secs = []
    for v, bs in villages.items():
        links = ''.join(
            f'<a href="/branch/{b["id"]}.html"><span>{esc(b["t"])}</span><span class="pg">书第{b["p"]}页</span></a>'
            for b in bs)
        q = v + ' ' + ' '.join(b['t'] for b in bs)
        if '小湴' in v:
            q += ' 小滘 小滘村'
        fresh = ' <a class="fresh" href="https://fengshizupu.com/archives/a000100/" target="_blank" rel="noopener">最新资料</a>' if v == '良西镇小湴村' else ''
        secs.append(f'<div class="vsec" data-q="{esc(q)}"><div class="grp" id="{esc(v)}">{esc(v)}（{len(bs)} 个支系）{fresh}</div>{links}</div>')
    body = f'''<div class="wrap"><section class="block"><h2>村庄索引</h2>
<p class="note">按原书世系目录标题中出现的村名整理：同一个村可能有多个房支，同一房支也可能分布在多个村。点村名看该村涉及的支系。</p>
<div class="vsearch"><input id="vq" type="text" placeholder="输入村名或支系名，如：小湴、那龙、凝斋" autocomplete="off"><div class="vcount" id="vcount"></div></div>
<div class="list">{"".join(secs)}</div></section></div>
<script>
var vq = document.getElementById('vq'), vc = document.getElementById('vcount');
var vsecs = Array.prototype.slice.call(document.querySelectorAll('.vsec'));
vq.addEventListener('input', function(){{
  var s = vq.value.trim(), n = 0;
  vsecs.forEach(function(x){{ var show = !s || x.getAttribute('data-q').indexOf(s) >= 0;
    x.style.display = show ? '' : 'none'; if (show) n++; }});
  vc.textContent = s ? ('找到 ' + n + ' 个村') : '';
}});
</script>'''
    w('villages.html', page('村庄索引｜恩平冯氏族谱', body, '', 'villages'))

    # ---------- buy ----------
    body = '''<div class="wrap"><section class="block"><h2>购买《恩平冯氏族谱》</h2>
<div class="kv">
<div>本站供宗亲免费在线查阅全书图片。</div>
<div>如需购买全书电子版（PDF 全本），请加微信联系：</div>
<div style="font-size:22px;color:#742f32;font-weight:700;margin:10px 0">微信：hola24</div>
<div>加微信时请注明来意（例如：购买恩平冯氏族谱），以便通过。</div>
</div></section></div>'''
    w('buy.html', page('购买联系｜恩平冯氏族谱', body, '', 'buy'))

    # ---------- reader ----------
    branch_js = [{'id': b['id'], 't': b['t'], 'zu': b.get('zu', ''), 'fang': b.get('fang', ''),
                  'from': b['p'] + BOOK_OFFSET, 'to': (b.get('end') or b['p']) + BOOK_OFFSET}
                 for b in branches]
    body = f'''
<div class="readerbar">
<a class="nav" href="/">首页</a>
<span class="info" id="info"></span>
<span class="info" id="branchInfo"></span>
<span style="flex:1"></span>
<label class="info">书页 <input id="jump" type="number" min="1" max="{BOOK_MAX}"></label>
<button class="primary" id="jumpBtn">跳页</button>
</div>
<div class="readerwrap">
<img class="pageimg" id="pg" alt="族谱原书页">
<div class="pagenav"><a id="prev" href="#">← 上一页</a><a id="next" href="#">下一页 →</a></div>
</div>
<script>
const TOTAL = {TOTAL_PDF}, OFF = {BOOK_OFFSET}, BMAX = {BOOK_MAX};
const BR = {json.dumps(branch_js, ensure_ascii=False)};
function label(n){{ if(n<=17) return '卷首第'+n+'页'; if(n<=30) return '目录第'+(n-17)+'页';
  if(n<=43) return '目录第'+(n-30)+'页';
  if(n<=BMAX+OFF) return '书第'+(n-OFF)+'页'; return '封底'; }}
let p = parseInt(new URLSearchParams(location.search).get('p') || '31');
if(!(p>=1 && p<=TOTAL)) p = 31;
const img = document.getElementById('pg');
function render(){{
  img.src = '/pages/p' + String(p).padStart(4,'0') + '.webp';
  img.alt = '《恩平冯氏族谱》' + label(p);
  document.getElementById('info').innerHTML = '<b>' + label(p) + '</b>（全书图第' + p + '页）';
  const bs = BR.filter(x => p>=x.from && p<=x.to);
  document.getElementById('branchInfo').innerHTML = bs.length ?
    '所属支系：' + bs.map(x => '<a href="/branch/' + x.id + '.html"><b>' + x.t + '</b></a>').join('、') : '';
  const pv = document.getElementById('prev'), nx = document.getElementById('next');
  pv.className = p<=1 ? 'off' : ''; nx.className = p>=TOTAL ? 'off' : '';
  pv.onclick = e => {{ e.preventDefault(); if(p>1){{ p--; sync(); }} }};
  nx.onclick = e => {{ e.preventDefault(); if(p<TOTAL){{ p++; sync(); }} }};
  window.scrollTo(0,0);
}}
function sync(){{ history.replaceState(null,'','?p='+p); render(); }}
document.getElementById('jumpBtn').onclick = () => {{
  const v = parseInt(document.getElementById('jump').value);
  if(v>=1 && v<=BMAX){{ p = v + OFF; sync(); }} }};
document.addEventListener('keydown', e => {{
  if(e.key==='ArrowLeft' && p>1){{ p--; sync(); }}
  if(e.key==='ArrowRight' && p<TOTAL){{ p++; sync(); }} }});
render();
</script>'''
    w('reader.html', head('看原书｜恩平冯氏族谱') + header('toc') + body + FAB + '</body></html>')

    # ---------- 404 ----------
    w('404.html', page('没有这一页', '<div class="wrap"><section class="block"><h2>没有这一页</h2><p>回到<a href="/">首页</a>重新查找。</p></section></div>'))

    # ---------- sitemap ----------
    urls = ['/', '/toc.html', '/villages.html', '/buy.html'] + [f'/branch/{b["id"]}.html' for b in branches]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + \
         ''.join(f'<url><loc>https://enping.fengshizupu.com{u}</loc></url>\n' for u in urls) + '</urlset>'
    with open(os.path.join(SITE, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sm)
    with open(os.path.join(SITE, 'robots.txt'), 'w', encoding='utf-8') as f:
        f.write('User-agent: *\nAllow: /\nSitemap: https://enping.fengshizupu.com/sitemap.xml\n')
    print('generated:', len(urls), 'urls,', len(branches), 'branches,', len(villages), 'villages')

def w(name, content):
    path = os.path.join(SITE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    build(load_data())
