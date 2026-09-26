(() => {
  const RAMP = ['void', 'carbon', 'graphite', 'iron', 'slate', 'pewter', 'steel', 'ash', 'fog', 'chalk', 'paper'];
  const ANSI = { red: 0, green: 130, yellow: 48, blue: 212, magenta: 300, cyan: 185, orange: 25 };
  const LIGHTNESS = { true: [5, 8, 11, 15, 22, 31, 40, 51, 64, 79, 90], false: [84, 90, 86, 79, 64, 54, 43, 35, 31, 15, 5] };
  const TOKENS = [...RAMP, 'accent'].map(k => [k, '--color-' + k]).concat(Object.keys(ANSI).map(k => [k, '--ansi-' + k]));
  const hsl = hex => {
    const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2, d = max - min;
    if (!d) return [0, 0, l * 100];
    const h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return [h * 60, d / (1 - Math.abs(2 * l - 1)) * 100, l * 100];
  };
  const hex = (h, s, l) => {
    s /= 100; l /= 100;
    const f = n => { const k = (n + h / 30) % 12; return l - s * Math.min(l, 1 - l) * Math.max(-1, Math.min(k - 3, 9 - k, 1)); };
    return '#' + [0, 8, 4].map(n => Math.round(f(n) * 255).toString(16).padStart(2, '0')).join('');
  };
  // ponytail: plain hsl steps copied from the sumi/kami greys, uneven across hues; move to oklch if a hue reads too bright
  const generateTheme = (seed, dark) => {
    const [h, s] = hsl(seed);
    const colors = Object.fromEntries(RAMP.map((k, i) => [k, hex(h, Math.min(s, 30), LIGHTNESS[dark][i])]));
    colors.accent = hex(h, Math.min(Math.max(s, 35), 80), dark ? 72 : 32);
    for (const [k, hue] of Object.entries(ANSI)) colors[k] = hex(hue, 55, dark ? 70 : 36);
    return { dark, colors };
  };
  const mori = generateTheme('#4f7d4a', true);
  mori.colors.accent = hex(30, 45, 62);
  const THEMES = { sumi: null, kami: null, taiyo: generateTheme('#b98a52', false), sakura: generateTheme('#e58fb0', true),
    umi: generateTheme('#3d7fd9', true), mori };
  const FONTS = [['mono', 'mono'], ['serif', 'serif'], ['inter', 'inter']];
  const root = document.documentElement;
  const os = matchMedia('(prefers-color-scheme: light)');
  const palette = (s, name) => name in THEMES ? THEMES[name] : (Array.isArray(s.themes) ? s.themes : []).find(t => t?.name === name);
  const themeChoices = s => [['', 'auto'], ...Object.keys(THEMES).map(k => [k, k]),
    ...(Array.isArray(s.themes) ? s.themes : []).map(t => [t.name, t.name])];
  const cached = () => { try { return JSON.parse(localStorage.getItem('settings')) || {}; } catch { return {}; } };
  let last = {}, painted;
  const apply = s => {
    last = s;
    const chosen = palette(s, s.theme) !== undefined ? s.theme : '';
    const theme = chosen || (os.matches ? 'kami' : 'sumi');
    const p = palette(s, theme);
    if (root.dataset.theme !== theme) root.dataset.theme = theme;
    for (const [k, v] of TOKENS) p ? root.style.setProperty(v, p.colors[k]) : root.style.removeProperty(v);
    for (const [v, dark, light] of [['--on-accent', 'var(--color-void)', 'var(--color-carbon)'], ['--logo', 'none', 'invert(1)'], ['color-scheme', 'dark', 'light']])
      p ? root.style.setProperty(v, p.dark ? dark : light) : root.style.removeProperty(v);
    root.dataset.font = s.font || 'mono';
    root.dataset.uiFont = s.ui_font || 'mono';
    const sel = document.getElementById('theme-sel');
    if (sel) sel.innerHTML = optionTags(themeChoices(s), chosen);
    const key = theme + JSON.stringify(p);
    if (painted !== undefined && painted !== key) dispatchEvent(new Event('theme-changed'));
    painted = key;
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
  window.THEME_TOKENS = TOKENS.map(([k]) => k);
  window.generateTheme = generateTheme;
  window.themePalette = name => palette(last, name);
  window.currentSettings = () => last;
  window.settings = api('/api/settings').then(cacheAndApply).catch(cached);

  document.head.insertAdjacentHTML('beforeend', '<link rel="stylesheet" href="/api/fonts.css">');
  window.fontChoices = api('/api/fonts').then(({ fonts }) => fonts).catch(() => [])
    .then(fonts => [...FONTS, ...fonts.map(f => [f, f.replace(/\.\w+$/, '')])]);

  window.saveSettings = patch => {
    apply({ ...cached(), ...patch });
    return api('/api/settings', JSON.stringify(patch)).then(cacheAndApply)
      .catch(e => { apply(cached()); throw e; });
  };

  window.themeSelector = () => `<select id="theme-sel" aria-label="Theme">${optionTags(themeChoices(last), palette(last, last.theme) !== undefined ? last.theme : '')}</select>`;

  window.pickTheme = t => saveSettings({ theme: t }).catch(() => {});
})();
