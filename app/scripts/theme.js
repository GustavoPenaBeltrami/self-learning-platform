(() => {
  const THEMES = { sumi: 'sumi', kami: 'kami' };
  const FONTS = [['mono', 'mono'], ['serif', 'serif'], ['inter', 'inter']];
  const root = document.documentElement;
  const current = () => root.dataset.theme || (matchMedia('(prefers-color-scheme: light)').matches ? 'kami' : 'sumi');
  const cached = () => { try { return JSON.parse(localStorage.getItem('settings')) || {}; } catch { return {}; } };
  const apply = s => {
    if (THEMES[s.theme]) root.dataset.theme = s.theme; else delete root.dataset.theme;
    root.dataset.font = s.font || 'mono';
    root.dataset.uiFont = s.ui_font || 'mono';
    const sel = document.getElementById('theme-sel');
    if (sel) sel.value = current();
    dispatchEvent(new CustomEvent('settings-applied', { detail: s }));
  };
  const cacheAndApply = s => {
    try { localStorage.setItem('settings', JSON.stringify(s)); } catch {}
    apply(s);
    return s;
  };

  window.api = (url, body) => fetch(url, body === undefined ? {} : { method: 'POST', body })
    .then(r => r.json()).then(r => { if (r.error) throw new Error(r.error); return r; });

  window.esc = s => String(s).replace(/[<>&"]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]));

  window.optionTags = (pairs, value) => pairs.map(([k, name]) =>
    `<option value="${esc(k)}"${k === value ? ' selected' : ''}>${esc(name)}</option>`).join('');

  // ponytail: localStorage only paints before the server answers, a settings.json edited by hand flashes once; drop the cache if the flash never matters
  apply(cached());
  window.THEMES = THEMES;
  window.settings = api('/api/settings').then(cacheAndApply).catch(cached);

  document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="/api/fonts.css">');
  window.fontChoices = api('/api/fonts').then(({ fonts }) => fonts).catch(() => [])
    .then(fonts => [...FONTS, ...fonts.map(f => [f, f.replace(/\.\w+$/, '')])]);

  window.saveSettings = patch => {
    apply({ ...cached(), ...patch });
    return api('/api/settings', JSON.stringify(patch)).then(cacheAndApply)
      .catch(e => { apply(cached()); throw e; });
  };

  window.themeSelector = () => `<select id="theme-sel" aria-label="Theme">${optionTags(Object.entries(THEMES), current())}</select>`;

  window.pickTheme = t => saveSettings({ theme: t }).catch(() => {});
})();
