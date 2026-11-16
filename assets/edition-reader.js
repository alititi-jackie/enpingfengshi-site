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
  const previous = document.getElementById('editionPrev');
  const next = document.getElementById('editionNext');
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
    updateReaderURL(page);
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

  const showMode = bindReaderControls({
    previous, next,
    move: (value, relative) => go(relative ? current + value : value),
    setMode(mode) {
      continuous = mode === 'scroll';
      showMode(mode);
      go(current);
    },
    jumpTo: value => Number.isInteger(value) && value >= 1 && value <= sheets.length ? value : undefined,
    dialog: viewer.dialog,
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

  showMode('scroll');
  const initial = readerPage(1, sheets.length);
  go(initial, false);
  requestAnimationFrame(() => {
    if (current > 1) go(current);
    initialized = true;
  });
}
