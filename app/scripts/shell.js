(() => {
  const PAGES = [['notes', 'notes.html'], ['exams', 'exam.html'], ['cards', 'cards.html'], ['project', 'project.html'], ['settings', 'settings.html']];

  window.key = (k, text, extra = '') => `<button class="key ${extra}"><kbd>${k}</kbd><span>${text}</span></button>`;

  window.noTopicsRow = cols => `<tr class="no-topics"><td colspan="${cols}"><img class="brand" src="/app/assets/lockup-stacked.png" alt="独学 Self Learning Platform"><span class="sub">no topics yet: ask your agent to "create a new topic" (slp-init)</span></td></tr>`;

  window.promptLine = (dir, cmd) => `<p class="prompt"><span class="p-host">notes</span> <span class="p-dir">${esc(dir)}</span> <span class="p-sig">❯</span> ${esc(cmd)}</p>`;

  window.folder = (name, count, body, current = false, title = name) => `<details open${current ? ' class="current"' : ''}>
    <summary title="${esc(title)}"><span class="name">${esc(name)}</span><span class="count">${count}</span></summary>${body}</details>`;

  window.offline = e => {
    const down = !e || e instanceof TypeError;
    return `<div class="sheet"><p class="prompt"><span class="p-sig">✕</span> ${down ? 'server not running' : esc(e.message)}</p>
      ${down ? '<p>open a terminal in the repo and run <code>uv run slp</code></p>' : ''}</div>`;
  };

  window.hotkey = spec => {
    const parts = spec.toLowerCase().split('+'), k = parts.pop();
    return e => ['ctrl', 'alt', 'shift', 'meta'].every(m => e[m + 'Key'] === parts.includes(m))
      && e.code === (/\d/.test(k) ? 'Digit' : 'Key') + k.toUpperCase();
  };

  window.placeNear = (el, anchor, gap = 8, center = false) => {
    const r = anchor.getBoundingClientRect();
    const x = center ? r.left + r.width / 2 - el.offsetWidth / 2 : r.left;
    el.style.left = Math.max(8, Math.min(x, innerWidth - el.offsetWidth - 8)) + 'px';
    el.style.top = (r.bottom + gap + el.offsetHeight > innerHeight ? r.top - el.offsetHeight - gap : r.bottom + gap) + 'px';
  };

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
    menu.className = 'drop-menu float';
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
      if (e.key === 'Escape') { e.stopPropagation(); closeDrop(); anchor.focus(); }
    };
    document.body.append(menu);
    placeNear(menu, anchor, 6);
    anchor.setAttribute('aria-expanded', 'true');
    drop = { anchor, menu };
    if (focus) (menu.querySelector('[aria-selected="true"]') || menu.firstChild)?.focus();
  };
  document.addEventListener('mousedown', e => {
    if (drop && !drop.menu.contains(e.target) && !drop.anchor.contains(e.target)) closeDrop();
  });
  addEventListener('keydown', e => {
    if (e.key === 'Escape' && drop) { closeDrop(); e.stopImmediatePropagation(); }
  });

  window.dropdown = sel => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'drop';
    btn.setAttribute('aria-haspopup', 'listbox');
    for (const a of ['data-tip', 'aria-label', 'title']) if (sel.hasAttribute(a)) btn.setAttribute(a, sel.getAttribute(a));
    sel.hidden = true;
    sel.after(btn);
    if (sel.labels?.[0]) { btn.id = sel.id + '-btn'; sel.labels[0].htmlFor = btn.id; }
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

  window.cardForm = async (slug, card = {}) => {
    const url = '/api/cards/' + encodeURIComponent(slug);
    const t = document.createElement('template');
    t.innerHTML = (await api('/api/topic/' + encodeURIComponent(slug)).catch(() => ({}))).html || '';
    let h1 = '';
    const notes = [...t.content.querySelectorAll('h1, h2')].map(h => {
      const text = h.textContent.trim();
      return h.tagName === 'H1' ? (h1 = text) : h1 ? `${h1} › ${text}` : text;
    });
    const dlg = document.createElement('dialog');
    dlg.className = 'card-form float';
    dlg.innerHTML = `<form>
      <p class="frame-title">${card.id ? 'edit card' : 'new card'}</p>
      <label>front<textarea name="front" rows="2" placeholder="a question">${esc(card.front || '')}</textarea></label>
      <label>back<textarea name="back" rows="3" placeholder="the answer, one or two sentences">${esc(card.back || '')}</textarea></label>
      <label>note<input name="note" list="card-notes" value="${esc(card.note || '')}" placeholder="H1 › H2" autocomplete="off"></label>
      <datalist id="card-notes">${[...new Set(notes)].map(n => `<option value="${esc(n)}">`).join('')}</datalist>
      <p class="minor" role="status"></p>
      <div class="keys">${key('⌘⏎', 'Save', 'cta')}${key('Esc', 'Cancel')}</div>
    </form>`;
    document.body.append(dlg);
    const form = dlg.querySelector('form'), [saveBtn, cancelBtn] = dlg.querySelectorAll('.key');
    return new Promise(done => {
      let result = null;
      const save = async () => {
        const f = Object.fromEntries(new FormData(form));
        try {
          result = await api(url, JSON.stringify({ upsert: card.id ? { id: card.id, ...f } : f }));
          dlg.close();
        } catch (e) {
          dlg.querySelector('[role=status]').textContent = '✕ ' + e.message;
        }
      };
      saveBtn.type = cancelBtn.type = 'button';
      saveBtn.onclick = save;
      cancelBtn.onclick = () => dlg.close();
      dlg.addEventListener('keydown', e => {
        e.stopPropagation();
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); save(); }
      });
      dlg.addEventListener('close', () => { dlg.remove(); done(result); });
      dlg.showModal();
      form.elements[card.front ? 'back' : 'front'].focus();
    });
  };

  window.deleteCard = (slug, card) => confirm(`delete the card "${card.front}"?`)
    ? api('/api/cards/' + encodeURIComponent(slug), JSON.stringify({ delete: card.id })) : Promise.resolve(null);

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
          <span id="status" role="status"></span>
          <span class="sl-ctl" hidden><button id="session" type="button"></button></span>
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
      width: { key: 'width', fallback: 960,
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

    const params = new URLSearchParams(location.search);
    const topic = params.get('topic') || (params.get('f') || '').match(/^topics\/([^/]+)\//)?.[1];
    if (topic) {
      const btn = document.getElementById('session'), url = '/api/session/' + encodeURIComponent(topic);
      let state = {};
      const hm = m => [m / 60 | 0, m % 60].map(n => String(n).padStart(2, '0')).join(':');
      const sync = async body => {
        try { state = await api(url, body); } catch { return; }
        const m = state.open ? Math.max(0, (Date.now() - new Date(state.started)) / 60000 | 0) : 0;
        btn.textContent = state.open ? `● ${hm(m)} ■` : '▶ session';
        btn.classList.toggle('on', state.open);
        btn.title = state.open ? `session since ${state.started.slice(11)}, click to stop` : 'start a study session';
        btn.parentElement.hidden = false;
      };
      btn.onclick = () => sync(JSON.stringify({ action: state.open ? 'stop' : 'start' }));
      sync();
      setInterval(sync, 30000);
    }

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
