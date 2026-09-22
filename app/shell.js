(() => {
  const PAGES = [['notes', 'notes.html'], ['exams', 'exam.html']];

  window.mountShell = current => {
    document.body.insertAdjacentHTML('afterbegin', `
      <header class="waybar">
        <div class="wb-left">
          <span class="wb-logo" aria-hidden="true"><svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10 5.2C8.4 4 6.2 3.5 3 3.5v11.8c3.2 0 5.4.5 7 1.7 1.6-1.2 3.8-1.7 7-1.7V3.5c-3.2 0-5.4.5-7 1.7z"/><path d="M10 5.2V17"/></svg></span>
          <nav class="wb-mod workspaces">${PAGES.map(([name, href], i) =>
            `<a href="${href}"${name === current ? ' aria-current="page"' : ''}>${i + 1}<span>${name}</span></a>`).join('')}</nav>
        </div>
        <div class="wb-center"><span class="wb-mod clock" id="clock"></span></div>
        <div class="wb-right">
          <div class="wb-tools" id="tools"></div>
          <div class="wb-mod"><span class="label">theme</span>${themeSelector()}</div>
        </div>
      </header>
      <div class="shell-body">
        <aside class="explorer"><div class="frame">
          <span class="frame-title">explorer</span>
          <nav class="tree" id="tree"></nav>
        </div></aside>
        <main class="panel" id="app"></main>
      </div>
      <footer class="statusline">
        <span class="mode" id="mode">NORMAL</span>
        <span class="sl-path" id="path">~/notes</span>
        <span class="sl-right">
          <span id="status"></span>
          <span class="sl-ctl" title="Content zoom">
            <svg viewBox="0 0 20 20" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="8.5" cy="8.5" r="5.5"/><path d="m12.7 12.7 4.8 4.8"/></svg>
            <button data-setting="zoom" data-step="-10" aria-label="Zoom out">−</button><input id="zoom" type="number" min="50" max="250" step="10" aria-label="Zoom in %">%<button data-setting="zoom" data-step="10" aria-label="Zoom in">+</button>
          </span>
          <span class="sl-ctl" title="Text width">
            <span aria-hidden="true">↔</span>
            <button data-setting="width" data-step="-40" aria-label="Narrower">−</button><input id="width" type="number" min="320" max="2400" step="20" aria-label="Width in px">px<button data-setting="width" data-step="40" aria-label="Wider">+</button>
          </span>
          <span class="sl-mod">utf-8[unix]</span>
          <span class="pos" id="pos">Top</span>
        </span>
      </footer>`);

    document.getElementById('theme-sel').onchange = e => pickTheme(e.target.value);

    const clock = document.getElementById('clock');
    const tick = () => {
      const d = new Date();
      clock.textContent = d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' }).replace(',', '')
        + '   ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    };
    tick();
    setInterval(tick, 15000);

    const app = document.getElementById('app');
    const SETTINGS = {
      zoom: { key: 'zoom', fallback: 100, apply: v => app.style.zoom = v / 100 },
      width: { key: 'width-' + current, fallback: current === 'notes' ? 736 : 960,
               apply: v => document.documentElement.style.setProperty('--width', v + 'px') },
    };
    const adjust = (name, value) => {
      const s = SETTINGS[name], field = document.getElementById(name);
      const v = Math.min(+field.max, Math.max(+field.min, Math.round(+value || s.fallback)));
      field.value = v;
      s.apply(v);
      localStorage.setItem(s.key, v);
    };
    Object.entries(SETTINGS).forEach(([name, s]) => {
      adjust(name, localStorage.getItem(s.key) || s.fallback);
      document.getElementById(name).onchange = e => adjust(name, e.target.value);
    });
    document.querySelectorAll('[data-setting]').forEach(b => b.onclick = () =>
      adjust(b.dataset.setting, +document.getElementById(b.dataset.setting).value + +b.dataset.step));

    const pos = document.getElementById('pos');
    const scroll = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      pos.textContent = max <= 0 ? 'All' : scrollY <= 0 ? 'Top' : scrollY >= max - 1 ? 'Bottom'
        : Math.round(scrollY / max * 100) + '%';
    };
    addEventListener('scroll', scroll, { passive: true });
    addEventListener('resize', scroll);
    new ResizeObserver(scroll).observe(document.body);

    return {
      app,
      tree: document.getElementById('tree'),
      tools: document.getElementById('tools'),
      path: t => document.getElementById('path').textContent = t,
      mode: (t, cls = '') => Object.assign(document.getElementById('mode'), { textContent: t, className: 'mode ' + cls }),
    };
  };
})();
