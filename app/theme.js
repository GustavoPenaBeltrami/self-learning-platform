(() => {
  const THEMES = { hypr: 'hypr', light: 'light', eink: 'e-ink', sakura: 'sakura', forest: 'forest', amber: 'amber crt' };
  const root = document.documentElement;
  const apply = t => { if (THEMES[t]) root.dataset.theme = t; else delete root.dataset.theme; };

  apply(localStorage.getItem('theme'));

  const current = () => root.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'hypr');

  window.themeSelector = () => `<select id="theme-sel" aria-label="Theme">${Object.entries(THEMES).map(([k, name]) =>
    `<option value="${k}"${k === current() ? ' selected' : ''}>${name}</option>`).join('')}</select>`;

  window.pickTheme = t => {
    apply(t);
    localStorage.setItem('theme', t);
  };
})();
