// Read-only browser assertion. Evaluate measureLayout.toString() in the preview.
export function measureLayout() {
  const width = document.documentElement.clientWidth;
  const rect = element => element.getBoundingClientRect();
  const headings = [...document.querySelectorAll('.section-heading h2')];
  const centerErrors = [document.querySelector('.site-header__inner'), ...headings].filter(Boolean).map(element => ({
    text: element.matches('h2') ? element.textContent : 'Header container',
    error: Math.abs(rect(element).left + rect(element).width / 2 - width / 2),
  }));
  const rowErrors = [];
  for (const selector of ['.how-steps', '.preset-grid', '.faq-grid']) {
    const grid = document.querySelector(selector);
    if (!grid) continue;
    const rows = new Map();
    for (const child of grid.children) {
      const r = rect(child), key = Math.round(r.top);
      if (!rows.has(key)) rows.set(key, []);
      rows.get(key).push(r.height);
    }
    for (const heights of rows.values()) if (heights.length > 1) rowErrors.push({selector, error: Math.max(...heights) - Math.min(...heights)});
  }
  const overflow = [...document.querySelectorAll('main *, .site-header *')].filter(el => {
    const r = rect(el), style = getComputedStyle(el);
    const closed = el.closest('details:not([open])');
    const hidden = closed && !el.closest('summary');
    return !hidden && r.width > 0 && style.position !== 'absolute' && style.position !== 'fixed' && !el.closest('.poe-tooltip') && (r.left < -1 || r.right > width + 1);
  }).map(el => ({tag:el.tagName, class:el.className, width:rect(el).width}));
  const forbidden = [...document.querySelectorAll('body *')].filter(el => {
    const style = getComputedStyle(el);
    return rect(el).width > 0 && (style.backgroundImage.includes('gradient(') || style.boxShadow !== 'none' || style.textShadow !== 'none' || style.filter.includes('blur('));
  }).map(el => el.className);
  return {width, centerErrors, rowErrors, overflow, forbidden,
    pageOverflow:document.documentElement.scrollWidth > width,
    pass:centerErrors.every(x => x.error <= 1) && rowErrors.every(x => x.error <= 1) && !overflow.length && !forbidden.length && document.documentElement.scrollWidth <= width};
}
