"""Publish independently maintained editions alongside the original Enping book."""
from collections import defaultdict
from hashlib import file_digest
from html import escape
import json
from pathlib import Path
import shutil
from urllib.parse import quote


INDEX = '/editions/'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def village_path(edition):
    return f"{INDEX}{edition['villageId']}/"


def edition_path(edition):
    return f"{village_path(edition)}{edition['year']}/{edition['archiveId']}/"


def edition_title(edition):
    return f"{edition['village']}{edition['branch']} · {edition['year']} 版"


def image_button(src, label, *, eager=False):
    loading = 'eager' if eager else 'lazy'
    return (f'<button type="button" class="reader-image edition-image" data-image="{escape(src)}" '
            f'data-label="{escape(label)}" aria-label="放大查看{escape(label)}">'
            f'<img class="pageimg" src="{escape(src)}" alt="{escape(label)}" loading="{loading}"></button>')


def image_dialog():
    return '''<dialog id="imageDialog" class="image-dialog" aria-labelledby="imageLabel">
<div class="image-toolbar"><span id="imageLabel"></span><button type="button" id="imageZoom">放大查看</button><button type="button" id="imageClose">关闭</button></div>
<div class="image-viewport"><img id="imageLarge" alt=""></div>
</dialog>
<script src="/assets/edition-reader.js"></script>'''


def build_editions(root, site, page, write, entry, search_box, old_villages):
    editions = read_json(Path(root) / 'data/village-editions.json')
    paths = [edition_path(edition) for edition in editions]
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate village edition path')
    by_village = defaultdict(list)
    search_entries, sitemap = [], []

    def publish(url, title, body, desc, *, index=True):
        if index:
            sitemap.append(url)
        document = page(title, f'<div class="wrap edition">{body}</div>', desc,
                        active='editions', url=url, index=index)
        write(f'{url.lstrip("/")}index.html', document)

    for edition in sorted(editions, key=lambda item: (-item['year'], item['villageId'], item['archiveId'])):
        by_village[edition['villageId']].append(edition)
        base = edition_path(edition)
        title = edition_title(edition)
        village = edition['village']
        keys = ' '.join([edition['town'], village, edition['branch'], *edition['aliases']])
        search_entries.append({'t': title, 'k': keys, 'kind': 'edition', 'url': base,
                               'detail': edition['source']})

        folder = Path(root) / base.strip('/')
        data = folder / 'data'
        archive_id = edition['archiveId']
        archive = next(item for item in read_json(data / 'archives.json') if item['id'] == archive_id)
        pages = sorted((item for item in read_json(data / 'archive_pages.json') if item['archiveId'] == archive_id),
                       key=lambda item: item['sequence'])
        pages_by_id = {item['id']: item for item in pages}
        if not pages or len(pages_by_id) != len(pages):
            raise ValueError(f'Invalid page list for {base}')
        media = folder / 'media'

        def media_url(relative):
            if not (media / relative).is_file():
                raise FileNotFoundError(media / relative)
            return f'{base}media/{relative}'

        original_pages = []
        for item in pages:
            relative = item['imagePath'].split(f'/archives/{archive_id}/', 1)[1]
            with (media / relative).open('rb') as image:
                if file_digest(image, 'sha256').hexdigest() != item['sha256']:
                    raise ValueError(f'Original checksum mismatch: {relative}')
            original_pages.append((media_url(relative), f"原谱第 {item['sequence']} 张"))
        shutil.copytree(media, Path(site) / base.strip('/') / 'media', dirs_exist_ok=True)

        sources = defaultdict(list)
        for source in read_json(data / 'person_sources.json'):
            if source['archivePageId'] in pages_by_id:
                sources[source['personId']].append(source)
        persons = {p['id']: p for p in read_json(data / 'persons.json') if p['id'] in sources}
        if set(persons) != set(sources):
            raise ValueError(f'Missing referenced people: {base}')
        parents, children = defaultdict(list), defaultdict(list)
        for rel in read_json(data / 'relationships.json'):
            if rel['type'] == 'parent_child' and rel['fromPersonId'] in persons and rel['toPersonId'] in persons:
                parents[rel['toPersonId']].append(rel['fromPersonId'])
                children[rel['fromPersonId']].append(rel['toPersonId'])

        def person_url(person_id):
            return f'{base}persons/{person_id}/'

        def sheet_url(page_id):
            return f'{base}pages/{page_id}/'

        def tree(person_id, relations, seen):
            branches = []
            for relative_id in dict.fromkeys(relations[person_id]):
                if relative_id in seen:
                    continue
                name = escape(persons[relative_id]['originalName'])
                branches.append(f'<details><summary>{name}</summary>'
                                f'<p><a href="{person_url(relative_id)}">查看人物资料</a></p>'
                                f'{tree(relative_id, relations, seen | {relative_id})}</details>')
            return '<div class="edition-tree">' + ''.join(branches) + '</div>' if branches else ''

        breadcrumb = (f'<p class="edition-crumb"><a href="{INDEX}">村庄更新资料</a> › '
                      f'<a href="{village_path(edition)}">{escape(village)}</a></p>')
        back = f'<p class="edition-crumb"><a href="{base}">{escape(title)}</a></p>'
        book = media_url(edition.get('bookFile', 'book.pdf'))
        catalog, person_rows = [], []
        for p in persons.values():
            pid = p['id']
            name = p['originalName']
            generation = f"第 {p['generationNumber']} 世" if p.get('generationNumber') else ''
            first = pages_by_id[sources[pid][0]['archivePageId']]['sequence']
            detail = ' · '.join(filter(None, (title, generation, f'谱页第 {first} 张')))
            person_keys = ' '.join([pid, p['normalizedName'], *p.get('aliases', [])])
            search_entries.append({'t': name, 'k': person_keys, 'kind': 'person', 'url': person_url(pid),
                                   'detail': detail})
            person_rows.append(entry(person_url(pid), name, detail,
                                     f' class="edition-person" data-q="{escape(name + " " + person_keys)}"'))
            origins = ''.join(entry(sheet_url(s['archivePageId']),
                                    f"查看第 {pages_by_id[s['archivePageId']]['sequence']} 张谱页",
                                    s['transcription']) for s in sources[pid])
            ancestors = tree(pid, parents, {pid}) or '<p>暂无更多已录关系</p>'
            descendants = tree(pid, children, {pid}) or '<p>暂无更多已录关系</p>'
            publish(person_url(pid), f'{name} · {title}',
                    f'{back}<section class="block"><h1>{escape(name)}</h1>'
                    f'<p>{escape(" · ".join(filter(None, (title, generation, pid))))}</p>'
                    f'<p>{escape(p.get("notes") or "")}</p><h2>原谱依据</h2><div class="list">{origins}</div></section>'
                    f'<section class="block"><h2>祖先关系</h2>{ancestors}'
                    f'<h2>后代关系</h2>{descendants}</section>',
                    f'查阅{name}在{title}中的人物资料、世系关系和谱页出处。', index=False)
        publish(f'{base}search/', f'查姓名 · {title}',
                f'{back}<section class="block"><h1>查姓名</h1><p>{escape(title)}</p>'
                f'{search_box("editionName", "输入姓名或人物编号", "editionCount")}'
                f'<div class="list">{"".join(person_rows)}</div></section>'
                '<script>filterList("editionName", "editionCount", ".edition-person", "位人物");</script>',
                f'按姓名或人物编号查找{title}收录的人物。', index=False)

        rendered = []
        for item in pages:
            pid = item['id']
            sequence = item['sequence']
            label = f"谱页 {sequence} · {item['chartHeader']}"
            jpg = media_url(f'typeset/{pid}.jpg')
            pdf = media_url(f'typeset/{pid}.pdf')
            rendered.append((jpg, label))
            catalog.append(f'<a class="card" href="{sheet_url(pid)}"><img src="{jpg}" alt="" loading="lazy">'
                           f'<span>{escape(label)}</span></a>')
            people_on_sheet = ''.join(entry(person_url(person['id']), person['originalName'], '')
                                      for person in persons.values()
                                      if any(source['archivePageId'] == pid for source in sources[person['id']]))
            publish(sheet_url(pid), f'{label} · {title}',
                    f'{back}<section class="block"><h1>{escape(label)}</h1>'
                    f'<p><a href="{pdf}" download>下载本页 PDF</a> · '
                    f'<a href="{base}originals/#original-{sequence}">查看本页原图</a></p>'
                    f'{image_button(jpg, label, eager=True)}</section>'
                    f'<section class="block"><h2>本页人物</h2><div class="list">{people_on_sheet}</div></section>'
                    f'{image_dialog()}', f'查看{title}的{label}与本页人物。')

        book_front = [(media_url('bookpages/cover.webp'), '封面'), (media_url('bookpages/fanli.webp'), '凡例')]
        book_index = [(media_url(f'bookpages/{file.name}'), f'全名索引 {number}')
                      for number, file in enumerate(sorted((media / 'bookpages').glob('index-*.webp'),
                                                          key=lambda part: int(part.stem.split('-')[-1])), 1)]
        full_book = book_front + rendered + book_index
        book_figures = ''.join(f'<figure data-sheet="{number}"><figcaption>{escape(label)}</figcaption>'
                               f'{image_button(src, label, eager=number == 1)}</figure>'
                               for number, (src, label) in enumerate(full_book, 1))
        publish(f'{base}read/', f'整版阅读 · {title}',
                f'{back}<section class="block"><h1>整版阅读 · {escape(title)}</h1>'
                f'<p><a href="{book}" download>下载整版 PDF</a></p>'
                '<div class="edition-reader-controls"><button type="button" id="editionPrev">上一页</button>'
                f'<label>整版页码 <input id="editionPage" type="number" min="1" max="{len(full_book)}" value="1"></label>'
                '<button type="button" id="editionNext">下一页</button>'
                '<button type="button" id="editionMode">连续阅读</button></div>'
                f'<div id="editionBook">{book_figures}</div></section>{image_dialog()}',
                f'在线翻阅{title}的封面、凡例、图式谱页和全名索引。', index=False)
        originals = ''.join(f'<figure id="original-{number}"><figcaption>{label}</figcaption>'
                            f'{image_button(src, label)}</figure>'
                            for number, (src, label) in enumerate(original_pages, 1))
        changes_file = data / 'changes.json'
        changes = read_json(changes_file) if changes_file.is_file() else []
        changes_link = changes_section = ''
        if changes:
            changes_link = '<p><a href="#changes">查看修改记录</a></p>'
            groups = []
            for group in changes:
                items = ''.join(f'<li>{escape(item)}</li>' for item in group['items'])
                groups.append(f'<h3>{escape(group["date"])}</h3><ul>{items}</ul>')
            changes_section = (
                '<section id="changes" class="block"><h2>修改记录</h2>'
                '<p>以下是宗亲核对后对网站人物资料和重排谱页所作的更正。'
                '原谱照片保留原貌。</p>' + ''.join(groups) + '</section>')
        publish(f'{base}originals/', f'原谱档案 · {title}',
                f'{back}<section class="block"><h1>原谱档案 · {escape(title)}</h1>'
                f'{changes_link}{originals}</section>{changes_section}{image_dialog()}',
                f'查看{title}的原谱照片与修改记录。', index=False)
        publish(base, title,
                f'{breadcrumb}<section class="block"><h1>{escape(title)}</h1>'
                f'<p>{escape(edition["source"])}</p><p>{escape(archive["rights"])}</p>'
                f'<p class="edition-links"><a href="{base}search/">查姓名</a>'
                f'<a href="{base}read/">整版阅读</a><a href="{book}" download>下载整版 PDF</a></p>'
                '<h2>在本档案中查姓名</h2>'
                f'{search_box("editionName", "输入姓名或人物编号", "editionCount")}'
                f'<div class="list edition-inline-people">{"".join(person_rows)}</div>'
                '<script>filterList("editionName", "editionCount", ".edition-person", "位人物", false);</script>'
                f'<h2>图式谱页</h2><div class="cards edition-catalog">{"".join(catalog)}</div>'
                f'<p><a class="btn" href="{base}originals/">原谱档案</a></p></section>',
                f'{edition["town"]}{village}{edition["branch"]}更新族谱，收录 {len(pages)} 张谱页，可查姓名、看世系。')

    village_rows = []
    for village_editions in by_village.values():
        first = village_editions[0]
        url = village_path(first)
        village_rows.append(entry(url, first['village'], first['town']))
        rows = ''.join(entry(edition_path(e), edition_title(e), e['source']) for e in village_editions)
        old = first.get('bookVillage')
        old_link = (f'<p><a href="/villages.html#{quote(old)}">查看原书村庄与房支</a></p>'
                    if old in old_villages else '')
        publish(url, first['village'],
                f'<p class="edition-crumb"><a href="{INDEX}">村庄更新资料</a></p>'
                f'<section class="block"><h1>{escape(first["village"])}</h1>'
                f'{old_link}<div class="list">{rows}</div></section>',
                f'查阅{first["town"]}{first["village"]}历年增修的族谱资料。')

    year_rows = []
    for year in sorted({e['year'] for e in editions}, reverse=True):
        rows = ''.join(entry(edition_path(e), edition_title(e), e['town']) for e in editions if e['year'] == year)
        year_rows.append(f'<h2>{year} 年</h2><div class="list">{rows}</div>')
    publish(INDEX, '村庄更新资料', '<section class="block"><h1>村庄更新资料</h1>'
            f'<h2>按村庄查阅</h2><div class="list">{"".join(village_rows)}</div>'
            f'{"".join(year_rows)}</section>',
            '按村庄和年份查阅各村后续增修的族谱资料。')
    return search_entries, sitemap, by_village
