(() => {
  const THEMES = { sumi: 'sumi', kami: 'kami', seed: 'seed' };
  const FONTS = [['mono', 'mono'], ['serif', 'serif'], ['inter', 'inter']];
  const root = document.documentElement;
  const os = matchMedia('(prefers-color-scheme: light)');
  const cached = () => { try { return JSON.parse(localStorage.getItem('settings')) || {}; } catch { return {}; } };
  let last = {}, painted;
  const apply = s => {
    last = s;
    const theme = THEMES[s.theme] ? s.theme : os.matches ? 'kami' : 'sumi';
    const seed = /^#[0-9a-f]{6}$/i.test(s.theme_seed || '') ? s.theme_seed : '';
    if (root.dataset.theme !== theme) root.dataset.theme = theme;
    seed ? root.style.setProperty('--seed', seed) : root.style.removeProperty('--seed');
    root.dataset.font = s.font || 'mono';
    root.dataset.uiFont = s.ui_font || 'mono';
    const sel = document.getElementById('theme-sel');
    if (sel) sel.value = THEMES[s.theme] ? s.theme : '';
    if (painted !== undefined && painted !== theme + seed) dispatchEvent(new Event('theme-changed'));
    painted = theme + seed;
    dispatchEvent(new CustomEvent('settings-applied', { detail: s }));
  };
  const cacheAndApply = s => {
    try { localStorage.setItem('settings', JSON.stringify(s)); } catch {}
    apply(s);
    return s;
  };
  os.addEventListener('change', () => apply(last));

  window.api = (url, body) => fetch(url, body === undefined ? {} : { method: 'POST', body }).then(async r => {
    const data = (r.headers.get('content-type') || '').includes('json') ? await r.json() : null;
    if (!r.ok || data?.error) throw Object.assign(new Error(data?.error || `${r.status} ${r.statusText}`), { status: r.status, data });
    return data;
  });

  window.esc = s => String(s).replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]));

  window.clean = html => {
    const t = document.createElement('template');
    t.innerHTML = html;
    t.content.querySelectorAll('script,iframe,frame,frameset,object,embed,style,link,meta,base,form,input,button,textarea,select,noscript,template')
      .forEach(n => n.remove());
    t.content.querySelectorAll('*').forEach(el => [...el.attributes].forEach(a => {
      const v = a.value.replace(/[\s\0-\x1f]/g, '');
      if (/^on/i.test(a.name) || a.name === 'srcdoc' || /^(javascript|vbscript|data:(?!image\/(png|jpe?g|gif|webp|avif);))/i.test(v))
        el.removeAttribute(a.name);
    }));
    return t.content;
  };

  window.optionTags = (pairs, value) => pairs.map(([k, name]) =>
    `<option value="${esc(k)}"${k === value ? ' selected' : ''}>${esc(name)}</option>`).join('');

  // ponytail: localStorage only paints before the server answers, a settings.json edited by hand flashes once; drop the cache if the flash never matters
  apply(cached());
  window.THEMES = THEMES;
  window.THEME_CHOICES = [['', 'auto'], ...Object.entries(THEMES)];
  window.settings = api('/api/settings').then(cacheAndApply).catch(cached);

  document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="/api/fonts.css">');
  window.fontChoices = api('/api/fonts').then(({ fonts }) => fonts).catch(() => [])
    .then(fonts => [...FONTS, ...fonts.map(f => [f, f.replace(/\.\w+$/, '')])]);

  window.saveSettings = patch => {
    apply({ ...cached(), ...patch });
    return api('/api/settings', JSON.stringify(patch)).then(cacheAndApply)
      .catch(e => { apply(cached()); throw e; });
  };

  window.themeSelector = () => `<select id="theme-sel" aria-label="Theme">${optionTags(THEME_CHOICES, THEMES[cached().theme] ? cached().theme : '')}</select>`;

  window.pickTheme = t => saveSettings({ theme: t }).catch(() => {});
})();
