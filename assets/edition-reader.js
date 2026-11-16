const viewer = bindImageDialog();
document.querySelectorAll('button[data-image]').forEach(button => {
  button.addEventListener('click', () => viewer.open(button.dataset.image, button.dataset.label));
});

const book = document.getElementById('editionBook');
if (book) {
  const sheets = [...book.querySelectorAll('[data-sheet]')];
  const bar = document.querySelector('.edition-readerbar');
  const info = document.getElementById('info');
  const jump = document.getElementById('jump');
  const jumpToggle = document.getElementById('jumpToggle');
  const previous = document.getElementById('editionPrev');
  const next = document.getElementById('editionNext');
  const single = document.getElementById('mSingle');
  const scroll = document.getElementById('mScroll');
  let continuous = true;
  let current = 0;
  let pendingFrame = false;
  let initialized = false;

  function updatePage(page) {
    current = page;
    const label = sheets[page - 1].querySelector('figcaption').textContent;
    const number = document.createElement('b');
    number.textContent = page;
    const detail = document.createElement('span');
    detail.className = 'full-only';
    detail.textContent = ' · ' + label;
    info.replaceChildren(number, '/' + sheets.length, detail);
    previous.disabled = page === 1;
    next.disabled = page === sheets.length;
    if (document.activeElement !== jump) jump.value = page;
    const url = new URL(location.href);
    url.searchParams.set('p', page);
    if (url.href !== location.href) history.replaceState(null, '', url);
  }

  function go(value, position = true) {
    const page = Math.min(sheets.length, Math.max(1, Number.parseInt(value, 10) || 1));
    updatePage(page);
    sheets.forEach((sheet, index) => { sheet.hidden = !continuous && index !== page - 1; });
    if (position) {
      if (continuous) sheets[page - 1].scrollIntoView({ block: 'start' });
      else window.scrollTo(0, 0);
    }
  }

  function setMode(mode) {
    continuous = mode;
    document.body.classList.toggle('scrollmode', mode);
    for (const [button, selected] of [[single, !mode], [scroll, mode]]) {
      button.classList.toggle('on', selected);
      button.setAttribute('aria-pressed', selected);
    }
    go(current);
  }

  function toggleJump(open) {
    document.body.classList.toggle('jumpon', open);
    jumpToggle.setAttribute('aria-expanded', open);
    if (open) jump.focus();
  }

  function submitJump() {
    if (!jump.value) return;
    const target = jump.value;
    jump.blur();
    toggleJump(false);
    go(target);
  }

  previous.onclick = () => go(current - 1);
  next.onclick = () => go(current + 1);
  single.onclick = () => setMode(false);
  scroll.onclick = () => setMode(true);
  jumpToggle.onclick = () => toggleJump(!document.body.classList.contains('jumpon'));
  document.getElementById('jumpBtn').onclick = submitJump;
  jump.addEventListener('keydown', event => {
    if (event.key === 'Enter') submitJump();
    if (event.key === 'Escape') {
      toggleJump(false);
      jumpToggle.focus();
    }
  });

  window.addEventListener('scroll', () => {
    if (!continuous || !initialized || pendingFrame) return;
    pendingFrame = true;
    requestAnimationFrame(() => {
      pendingFrame = false;
      if (!continuous) return;
      const threshold = bar.getBoundingClientRect().bottom + 32;
      let page = 1;
      for (const sheet of sheets) {
        if (sheet.getBoundingClientRect().top > threshold) break;
        page = Number(sheet.dataset.sheet);
      }
      if (page !== current) updatePage(page);
    });
  }, { passive: true });

  document.body.classList.add('scrollmode');
  const initial = Number.parseInt(new URLSearchParams(location.search).get('p'), 10);
  go(initial, false);
  requestAnimationFrame(() => {
    if (current > 1) go(current);
    initialized = true;
  });
}
