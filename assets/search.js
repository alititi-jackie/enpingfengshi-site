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
  return rows.filter(row => normalizeQuery(row.t + ' ' + row.k).includes(term))
    .sort((a, b) => Number(normalizeQuery(b.t) === term) - Number(normalizeQuery(a.t) === term));
}

function appendSearchResult(box, item) {
  const link = document.createElement('a');
  link.href = item.url;
  link.textContent = item.t;
  const detail = document.createElement('span');
  detail.className = 'pg';
  detail.textContent = item.detail;
  link.append(detail);
  box.append(link);
}

for (const form of document.querySelectorAll('[data-search-index]')) {
  const input = form.querySelector('input');
  const box = document.getElementById(form.dataset.results);
  const status = document.getElementById(form.dataset.status);
  const isHome = form.dataset.kind === 'home';
  const listAll = [...form.elements].find(element => element.hasAttribute('data-list-all'));
  let revision = 0;

  async function search({ submit = false, all = false } = {}) {
    const current = ++revision;
    const term = normalizeQuery(input.value);
    box.replaceChildren();
    status.textContent = '';
    if (!term && !all) return;
    status.textContent = '正在查找…';
    try {
      const data = await requestIndex(form.dataset.searchIndex);
      if (current !== revision) return;
      if (isHome && /^\d+$/.test(term)) {
        const match = data.numeric[Number(term)];
        status.textContent = match ? '' : '暂未找到这一个原书页码。';
        if (match) {
          if (submit) location.href = match.url;
          else appendSearchResult(box, match);
        }
        return;
      }
      let hits;
      if (isHome) {
        const collections = data.editions.filter(row => normalizeQuery(row.t + ' ' + row.k).includes(term));
        const original = data.original.filter(row => normalizeQuery(row.t + ' ' + row.k).includes(term)).slice(0, 12);
        const groups = await Promise.all(data.people.map(requestIndex));
        if (current !== revision) return;
        hits = [...collections, ...original, ...findPeople(groups.flat(), term).slice(0, 12)];
      } else {
        const pageNumber = form.dataset.pageIndex && term.match(/^(?:第)?(\d+)(?:页)?$/);
        if (pageNumber) {
          const pages = await requestIndex(form.dataset.pageIndex);
          if (current !== revision) return;
          const match = pages[Number(pageNumber[1])];
          status.textContent = match ? '' : '暂未找到这个谱页页码。';
          if (match) appendSearchResult(box, match);
          return;
        }
        hits = all ? data : findPeople(data, form.dataset.pageIndex || !/^\d+$/.test(term) ? term : 'p' + term);
      }
      const limit = all || isHome ? hits.length : 50;
      status.textContent = hits.length
        ? `找到 ${hits.length} 条相关记录${hits.length > limit ? `，显示前 ${limit} 条` : ''}`
        : '暂未找到相关记录，请换个关键词。';
      for (const result of hits.slice(0, limit)) appendSearchResult(box, result);
    } catch {
      if (current === revision) status.textContent = '搜索资料加载失败，请再试一次。';
    }
  }

  form.addEventListener('submit', event => { event.preventDefault(); search({ submit: true }); });
  input.addEventListener('input', () => search());
  listAll?.addEventListener('click', () => { input.value = ''; search({ all: true }); });
  const initial = new URLSearchParams(location.search).get('q');
  if (initial) {
    input.value = initial;
    search({ submit: isHome });
  }
}
