const requestIndex = (() => {
  const cache = new Map();
  return (url) => {
    if (!cache.has(url)) cache.set(url, fetch(url).then(response => {
      if (!response.ok) throw new Error('无法读取索引');
      return response.json();
    }).catch(error => {
      cache.delete(url);
      throw error;
    }));
    return cache.get(url);
  };
})();

function findPeople(rows, term) {
  const number = term.match(/^p(\d+)$/);
  if (number) return rows.filter(row => Number(row.id.slice(1)) === Number(number[1]));
  return matchingRows(rows, term);
}

function appendSearchResult(box, item) {
  const link = document.createElement('a');
  link.href = item.url;
  if (item.url.startsWith('/editions/')) link.className = 'edition-result';
  link.textContent = item.t;
  const detail = document.createElement('span');
  detail.className = 'pg';
  detail.textContent = item.detail;
  link.append(detail);
  box.append(link);
}

function pageQuery(term) {
  const scoped = term.match(/^(目录 *\(? *(前组|后组) *\)?|卷首) *(?:第 *)?(\d+) *(?:页|张)?$/);
  if (scoped) return { section: scoped[2] ? `目录（${scoped[2]}）` : '卷首', number: Number(scoped[3]) };
  const page = term.match(/^(?:第 *)?(\d+) *页?$/);
  if (page) return { number: Number(page[1]), bare: /^\d+$/.test(term) };
  const edition = term.match(/^(.+?) *(?:第 *)?(\d+) *页$/);
  if (edition) return { edition: edition[1].trim(), number: Number(edition[2]) };
  return null;
}

function matchingRows(rows, term) {
  return rows.filter(row => matchesSearch(normalizeQuery(row.t + ' ' + row.k), term))
    .sort((a, b) => Number(normalizeQuery(b.t) === term) - Number(normalizeQuery(a.t) === term));
}

async function sitePages(data, query, includeEditions) {
  const original = query.section
    ? data.scopedPages[query.section]?.[query.number]
    : query.edition ? null : data.numeric[query.number];
  const rows = original ? [{ ...original, t: '1995 年重修版 · ' + original.t }] : [];
  if (!includeEditions || query.section) return rows;
  const editions = query.edition ? matchingRows(data.editions, query.edition) : data.editions;
  const pages = await Promise.all(editions.map(async edition => {
    const index = await requestIndex(edition.pageIndex);
    const match = index[query.number];
    return match ? { ...match, t: `${edition.t} · 谱页第 ${query.number} 页` } : null;
  }));
  return [...rows, ...pages.filter(Boolean)];
}

function showGroup(box, label, rows) {
  if (!rows.length) return;
  const section = document.createElement('section');
  const heading = document.createElement('h2');
  heading.textContent = `${label}（${rows.length}）`;
  const list = document.createElement('div');
  list.className = 'list';
  for (const item of rows.slice(0, 12)) appendSearchResult(list, item);
  if (rows.length > 12) {
    const more = document.createElement('button');
    more.type = 'button';
    more.className = 'btn ghost';
    more.textContent = `显示更多${label}（${rows.length - 12}）`;
    more.addEventListener('click', () => {
      more.remove();
      for (const item of rows.slice(12)) appendSearchResult(list, item);
      list.children[12].focus();
    });
    list.append(more);
  }
  section.append(heading, list);
  box.append(section);
}

for (const form of document.querySelectorAll('[data-search-index]')) {
  const input = form.querySelector('input');
  const box = document.getElementById(form.dataset.results);
  const status = document.getElementById(form.dataset.status);
  const isHome = form.dataset.kind === 'home';
  const isToc = form.dataset.kind === 'toc';
  const tocRows = isToc ? [...document.querySelectorAll('#toclist > a')]
    .map(row => [row, normalizeQuery(row.dataset.q)]) : [];
  const listAll = [...form.elements].find(element => element.hasAttribute('data-list-all'));
  let revision = 0;

  function showCount(count, limit = count) {
    status.textContent = count
      ? `找到 ${count} 条相关记录${count > limit ? `，显示前 ${limit} 条` : ''}`
      : '暂未找到相关记录，请换个关键词。';
  }

  async function search({ all = false } = {}) {
    const current = ++revision;
    const term = normalizeQuery(input.value);
    const query = pageQuery(term);
    box.replaceChildren();
    status.textContent = '';
    if (isToc) {
      let count = 0;
      for (const [row, keys] of tocRows) {
        const visible = !term || (!query && matchesSearch(keys, term));
        row.style.display = visible ? '' : 'none';
        if (visible) count++;
      }
      if (!query) {
        if (term) showCount(count);
        return;
      }
    }
    if (!term && !all) return;
    status.textContent = '正在查找…';
    try {
      const data = await requestIndex(form.dataset.searchIndex);
      if (current !== revision) return;
      if (isHome || isToc) {
        if (query) {
          const rows = await sitePages(data, query, isHome);
          if (current !== revision) return;
          showCount(rows.length);
          if (isHome) showGroup(box, '谱页', rows);
          else for (const item of rows) appendSearchResult(box, item);
          return;
        }
        const groups = await Promise.all(data.people.map(requestIndex));
        if (current !== revision) return;
        const directory = /^p\d+$/.test(term) ? []
          : [...matchingRows(data.editions, term), ...matchingRows(data.original, term)];
        const people = findPeople(groups.flat(), term);
        showCount(directory.length + people.length);
        showGroup(box, '村庄、房支与目录', directory);
        showGroup(box, '人物', people);
        return;
      }

      let hits;
      if (form.dataset.pageIndex && query && !query.section && !query.edition) {
        const pages = await requestIndex(form.dataset.pageIndex);
        if (current !== revision) return;
        const match = pages[query.number];
        hits = match ? [match] : [];
        if (query.bare) {
          hits.push(...findPeople(data, 'p' + term).map(person => ({
            ...person,
            t: '人物 · ' + person.t,
            detail: person.id + ' · ' + person.detail,
          })));
        }
      } else {
        hits = all ? data : findPeople(data, !form.dataset.pageIndex && /^\d+$/.test(term) ? 'p' + term : term);
      }
      const limit = all ? hits.length : 50;
      showCount(hits.length, limit);
      for (const result of hits.slice(0, limit)) appendSearchResult(box, result);
    } catch {
      if (current === revision) status.textContent = '搜索资料加载失败，请再试一次。';
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); search(); });
  input.addEventListener('input', () => search());
  listAll?.addEventListener('click', () => { input.value = ''; search({ all: true }); });
  const initial = new URLSearchParams(location.search).get('q');
  if (initial) {
    input.value = initial;
    search();
  }
}
