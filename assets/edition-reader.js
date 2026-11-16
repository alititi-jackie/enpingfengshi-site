const viewer = bindImageDialog();
document.querySelectorAll('button[data-image]').forEach(button => {
  button.addEventListener('click', () => viewer.open(button.dataset.image, button.dataset.label));
});

const book = document.getElementById('editionBook');
if (book) {
  const sheets = Array.from(book.querySelectorAll('[data-sheet]'));
  const pageNumber = document.getElementById('editionPage');
  const previous = document.getElementById('editionPrev');
  const next = document.getElementById('editionNext');
  const mode = document.getElementById('editionMode');
  let continuous = false;
  let current = 1;

  function show(value, scrollToPage = false) {
    current = Math.min(sheets.length, Math.max(1, Number.parseInt(value, 10) || 1));
    pageNumber.value = current;
    previous.disabled = current === 1;
    next.disabled = current === sheets.length;
    sheets.forEach((sheet, index) => { sheet.hidden = !continuous && index !== current - 1; });
    const url = new URL(location.href);
    url.searchParams.set('p', current);
    history.replaceState(null, '', url);
    if (continuous && scrollToPage) sheets[current - 1].scrollIntoView();
  }

  previous.onclick = () => show(current - 1, true);
  next.onclick = () => show(current + 1, true);
  pageNumber.onchange = () => show(pageNumber.value, true);
  mode.onclick = () => {
    continuous = !continuous;
    mode.textContent = continuous ? '单页阅读' : '连续阅读';
    show(current, true);
  };
  show(new URLSearchParams(location.search).get('p'));
}
