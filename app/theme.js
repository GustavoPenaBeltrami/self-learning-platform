(() => {
  const THEMES = { hypr: 'hypr', light: 'light', eink: 'e-ink', sakura: 'sakura', forest: 'forest', amber: 'amber crt' };
  const root = document.documentElement;
  const current = () => root.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'hypr');
  const cached = () => { try { return JSON.parse(localStorage.getItem('settings')) || {}; } catch { return {}; } };
  const apply = s => {
    if (THEMES[s.theme]) root.dataset.theme = s.theme; else delete root.dataset.theme;
    root.dataset.font = s.font || 'mono';
    const sel = document.getElementById('theme-sel'), font = document.getElementById('font');
    if (sel) sel.value = current();
    if (font) font.value = root.dataset.font;
  };
  const keep = s => {
    if (s.error) throw new Error(s.error);
    try { localStorage.setItem('settings', JSON.stringify(s)); } catch {}
    apply(s);
    return s;
  };

  // ponytail: localStorage is only a paint cache against a theme flash; settings.json is the source of truth
  apply(cached());
  window.THEMES = THEMES;
  window.settings = fetch('/api/settings').then(r => r.json()).then(keep).catch(cached);

  window.saveSettings = patch => {
    apply({ ...cached(), ...patch });
    return fetch('/api/settings', { method: 'POST', body: JSON.stringify(patch) }).then(r => r.json()).then(keep)
      .catch(e => { apply(cached()); throw e; });
  };

  window.themeSelector = () => `<select id="theme-sel" aria-label="Theme">${Object.entries(THEMES).map(([k, name]) =>
    `<option value="${k}"${k === current() ? ' selected' : ''}>${name}</option>`).join('')}</select>`;

  window.pickTheme = t => saveSettings({ theme: t }).catch(() => {});
})();
