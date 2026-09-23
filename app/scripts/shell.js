(() => {
  const PAGES = [['notes', 'notes.html'], ['exams', 'exam.html'], ['project', 'project.html'], ['settings', 'settings.html']];

  window.key = (k, text, extra = '') => `<button class="key ${extra}"><kbd>${k}</kbd><span>${text}</span></button>`;

  window.noTopicsRow = cols => `<tr class="no-topics"><td colspan="${cols + 1}"><img class="brand" src="/app/assets/lockup-stacked.png" alt="独学 Self Learning Platform"><span class="sub">no topics yet: ask your agent to "create a new topic" (slp-init)</span></td></tr>`;

  let drop;
  window.closeDrop = () => {
    if (!drop) return;
    drop.menu.remove();
    drop.anchor.setAttribute('aria-expanded', 'false');
    drop = null;
  };
  window.dropMenu = (anchor, items, pick, current, focus = false) => {
    if (drop?.anchor === anchor) return closeDrop();
    closeDrop();
    const menu = document.createElement('div');
    menu.className = 'drop-menu';
    menu.setAttribute('role', 'listbox');
    menu.innerHTML = items.map(([v, label]) =>
      `<button type="button" role="option" data-v="${esc(v)}" aria-selected="${v === current}">${label}</button>`).join('');
    menu.onmousedown = e => e.preventDefault();
    menu.onclick = e => {
      const b = e.target.closest('[data-v]');
      if (!b) return;
      closeDrop();
      pick(b.dataset.v);
    };
    menu.onkeydown = e => {
      const all = [...menu.children], i = all.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        all[(i + (e.key === 'ArrowDown' ? 1 : -1) + all.length) % all.length].focus();
      }
      if (e.key === 'Escape') { closeDrop(); anchor.focus(); }
    };
    document.body.append(menu);
    const r = anchor.getBoundingClientRect();
    menu.style.left = Math.max(8, Math.min(r.left, innerWidth - menu.offsetWidth - 8)) + 'px';
    menu.style.top = (r.bottom + 6 + menu.offsetHeight > innerHeight ? r.top - menu.offsetHeight - 6 : r.bottom + 6) + 'px';
    anchor.setAttribute('aria-expanded', 'true');
    drop = { anchor, menu };
    if (focus) (menu.querySelector('[aria-selected="true"]') || menu.firstChild)?.focus();
  };
  document.addEventListener('mousedown', e => {
    if (drop && !drop.menu.contains(e.target) && !drop.anchor.contains(e.target)) closeDrop();
  });
  addEventListener('keydown', e => { if (e.key === 'Escape') closeDrop(); });

  window.dropdown = sel => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'drop';
    btn.setAttribute('aria-haspopup', 'listbox');
    for (const a of ['data-tip', 'aria-label', 'title']) if (sel.hasAttribute(a)) btn.setAttribute(a, sel.getAttribute(a));
    sel.hidden = true;
    sel.after(btn);
    const sync = () => btn.textContent = sel.selectedOptions[0]?.text ?? '';
    const value = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
    Object.defineProperty(sel, 'value', { get() { return value.get.call(this); }, set(v) { value.set.call(this, v); sync(); } });
    new MutationObserver(sync).observe(sel, { childList: true, subtree: true });
    btn.onmousedown = e => e.preventDefault();
    btn.onclick = e => dropMenu(btn, [...sel.options].map(o => [o.value, esc(o.text)]), v => {
      sel.value = v;
      sel.dispatchEvent(new Event('change'));
    }, sel.value, e.detail === 0);
    sync();
    return btn;
  };

  window.mountShell = current => {
    document.title = '独学 · ' + current;
    document.head.insertAdjacentHTML('beforeend', '<link rel="icon" href="/app/assets/favicon.svg">');
    document.body.insertAdjacentHTML('afterbegin', `
      <header class="waybar">
        <div class="wb-left">
          <a class="wb-logo" href="project.html" title="独学 · SLP"><img class="brand" src="/app/assets/mark.png" alt="独学" width="20" height="20"></a>
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
    dropdown(document.getElementById('theme-sel'));

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
