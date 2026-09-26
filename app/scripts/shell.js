(() => {
  const PAGES = [['notes', 'notes.html'], ['exams', 'exam.html'], ['cards', 'cards.html'], ['project', 'project.html'], ['settings', 'settings.html']];

  const ICON = {
    highlight: '<path d="M3.5 16.5h13"/><path d="M6.5 13.5 12.5 3.5l3.5 2.2-6 10.3z"/><path d="M6.5 13.5 10 15.7"/>',
    underline: '<path d="M6 3v5.5a4 4 0 0 0 8 0V3"/><path d="M4.5 16.8h11"/>',
    strike:    '<path d="M3.5 10h13"/><path d="M13.5 5.6a3.4 2.7 0 0 0-6.2 1.1c0 1.6 1.7 2.2 3.2 2.6"/><path d="M7 13.4a3.4 2.7 0 0 0 6.4-.6"/>',
    reference: '<path d="M8.6 11.4a3.2 3.2 0 0 0 4.5 0l2.6-2.6a3.2 3.2 0 0 0-4.5-4.5l-.9.9"/><path d="M11.4 8.6a3.2 3.2 0 0 0-4.5 0L4.3 11.2a3.2 3.2 0 0 0 4.5 4.5l.9-.9"/>',
    note:      '<path d="M4 3.5h12v8.5l-3.5 4H4z"/><path d="M16 12h-3.5v4"/>',
    flashcard: '<rect x="2.5" y="6" width="12" height="9" rx="1"/><path d="M5.5 6V3.5h12v9H14.5"/>',
    voice:     '<rect x="7.5" y="2.5" width="5" height="9" rx="2.5"/><path d="M4.5 9.5a5.5 5.5 0 0 0 11 0"/><path d="M10 15v2.5"/>',
    image:     '<rect x="3" y="4" width="14" height="12" rx="1.5"/><circle cx="7.3" cy="8" r="1.2"/><path d="M3.6 14.2 8 10l3 2.8 2.2-2 3.2 3"/>',
    remove:    '<path d="M5 5l10 10M15 5 5 15"/>',
    diagram:   '<rect x="7" y="2.5" width="6" height="4" rx="1"/><rect x="1.8" y="13.5" width="5.4" height="4" rx="1"/><rect x="12.8" y="13.5" width="5.4" height="4" rx="1"/><path d="M10 6.5v3M4.5 13.5v-2.5h11v2.5"/>',
    formula:   '<path d="M14.6 4.2H6.4l4.6 5.8-4.6 5.8h8.2"/>',
    plus:      '<path d="M10 4v12M4 10h12"/>',
    newset:    '<path d="M2.5 5.5h5l1.5 2h8.5v8.5h-15z"/><path d="M10 9.5v4.5M7.75 11.75h4.5"/>',
    edit:      '<path d="M4 16h3l8.5-8.5-3-3L4 13z"/><path d="M11 6l3 3"/>',
    trash:     '<path d="M4 6h12"/><path d="M8 6V4h4v2"/><path d="M5.5 6l.8 10h7.4l.8-10"/>',
    list:      '<path d="M7.5 5.5h9M7.5 10h9M7.5 14.5h9"/><path d="M3.5 5.5h.5M3.5 10h.5M3.5 14.5h.5"/>',
    skip:      '<path d="M5 5l6.5 5L5 15z"/><path d="M15 5v10"/>',
    due:       '<circle cx="10" cy="10" r="6.5"/><path d="M10 6.5V10l2.5 1.5"/>',
    back:      '<path d="M16 10H4"/><path d="M8.5 5.5 4 10l4.5 4.5"/>',
    info:      '<circle cx="10" cy="10" r="7"/><path d="M10 9v4.5"/><path d="M10 6.2v.1"/>',
  };
  window.svg = (n, t = 16) => `<svg viewBox="0 0 20 20" width="${t}" height="${t}" fill="none"
    stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${ICON[n]}</svg>`;

  let tip;
  window.closeTip = () => { tip?.remove(); tip = null; };
  const showTip = el => {
    closeTip();
    if (el.getAttribute('aria-expanded') === 'true') return;
    tip = document.createElement('div');
    tip.className = 'tip float';
    tip.textContent = el.dataset.keys ? keysTip(el.dataset.keys.split(' ')) : el.dataset.tip;
    el.removeAttribute('title');
    document.body.appendChild(tip);
    placeNear(tip, el, 6, true);
    el.addEventListener('mouseleave', closeTip, { once: true });
  };

  window.pad = n => String(n).padStart(2, '0');
  window.native = e => e.key === ' ' || e.key === 'Enter';
  window.key = (k, text, extra = '') => `<button class="key ${extra}"><kbd>${k}</kbd><span>${text}</span></button>`;

  window.noTopicsRow = cols => `<tr class="no-topics"><td colspan="${cols}"><img class="brand" src="/app/assets/lockup-stacked.png" alt="独学 Self Learning Platform"><span class="sub">no topics yet: ask your agent to "create a new topic" (slp-init)</span></td></tr>`;

  window.promptLine = (dir, cmd) => `<p class="prompt"><span class="p-host">独学</span> <span class="p-dir">${esc(dir)}</span> <span class="p-sig">❯</span> ${esc(cmd)}</p>`;

  window.folder = (name, count, body, current = false, title = name) => `<details${current ? ' open class="current"' : ''}>
    <summary title="${esc(title)}"><span class="name">${esc(name)}</span><span class="count">${count}</span></summary>${body}</details>`;
  window.SETTING_PAGES = [['global.html', 'global', 'profile, fonts, dictation model'],
    ['shortcuts.html', 'shortcuts', 'the key of every action, grouped by page'],
    ['card-config.html', 'cards', 'how many days a card waits at each step until it is learned'],
    ['themes.html', 'themes', 'the colors of the app: built-in themes and your own']];
  window.crumbs = parts => `<nav class="crumbs" aria-label="breadcrumb">${parts.map(([t, href], i) => href && i < parts.length - 1
    ? `<a href="${esc(href)}">${esc(t)}</a>` : `<span aria-current="page">${esc(t)}</span>`).join('<span class="sep">›</span>')}</nav>`;
  window.settingsCrumbs = (name, right = '') => `<div class="top">${crumbs([['settings', 'settings.html'], [name]])}${right}</div>`;
  window.configTree = current => folder('settings.json', SETTING_PAGES.length, '<ul>' + SETTING_PAGES.map(([href, name]) =>
    `<li><a href="${href}"${href === current ? ' aria-current="page"' : ''}><span class="n">›</span><span>${name}</span></a></li>`).join('') + '</ul>', true);

  window.offline = e => {
    const down = !e || e instanceof TypeError;
    return `<div class="sheet"><p class="prompt"><span class="p-sig">✕</span> ${down ? 'server not running' : esc(e.message)}</p>
      ${down ? '<p>open a terminal in the repo and run <code>uv run slp</code></p>' : ''}</div>`;
  };

  const MODS = ['ctrl', 'alt', 'shift', 'meta'];
  window.SHORTCUTS = [
    ['notes.dictate', 'ctrl+m', 'dictate, again to stop', 'notes'],
    ['notes.bold', '⌘B', 'bold', 'notes', 1],
    ['notes.italic', '⌘I', 'italic', 'notes', 1],
    ['notes.heading', '/h1…/h6', 'heading, at line start', 'notes', 1],
    ['notes.list', '- or 1.', 'list, at line start', 'notes', 1],
    ['notes.ref', '[[name]]', 'reference to a section', 'notes', 1],
    ['notes.close', 'Esc', 'close menus and previews', 'notes', 1],
    ['exam.grade', 'enter', 'finish exam', 'exam'],
    ['exam.record', 'r', 'record, again to stop (oral)', 'exam'],
    ['exam.write', 't', 'answer in writing (oral)', 'exam'],
    ['exam.retake', 'enter', 'retake', 'exam.results'],
    ['exam.back', 'Esc', 'back', 'exam exam.topic exam.results', 1],
    ['cards.due', 'enter', 'study due', 'cards.sets cards.list'],
    ['cards.all', 'a', 'study all', 'cards.sets cards.empty cards.list cards.study'],
    ['cards.newset', 'c', 'new set', 'cards.sets'],
    ['cards.new', 'n', 'new card', 'cards.sets cards.empty cards.list cards.study'],
    ['cards.list', 'l', 'list', 'cards.sets cards.empty cards.study cards.done'],
    ['cards.reveal', 'space', 'reveal', 'cards.study'],
    ['cards.edit', 'e', 'edit', 'cards.study'],
    ['cards.skip', 's', 'skip', 'cards.study'],
    ['cards.delete', 'd', 'delete', 'cards.study'],
    ['cards.forgot', '1', "don't know", 'cards.reveal'],
    ['cards.knew', '2', 'knew it', 'cards.reveal'],
    ['cards.unsure', '3', 'unsure', 'cards.reveal'],
    ['cards.again', 'enter', 'study again', 'cards.done'],
    ['cards.back', 'Esc', 'back', 'cards.sets cards.empty cards.list cards.study cards.done', 1],
    ['cards.close', 'Esc', 'back to the card', 'cards.reveal', 1],
    ['cards.save', '⌘⏎', 'save the card form', 'cards.sets cards.empty cards.list cards.study notes', 1],
    ['notes.menus', '↑ ↓ · Esc', 'move in a dropdown · close it', 'notes', 1],
  ].map(([id, key, text, modes, fixed]) => ({ id, key, text, modes: modes.split(' '), fixed: !!fixed }));
  const byId = Object.fromEntries(SHORTCUTS.map(s => [s.id, s]));
  window.shortcut = id => byId[id].fixed ? byId[id].key : currentSettings().shortcuts?.[id] || byId[id].key;
  window.keyLabel = spec => spec.split('+').map(p => ({ meta: '⌘', space: 'Space', enter: '⏎' })[p] || (p.length === 1 ? p.toUpperCase() : p)).join('+');
  window.keyFor = id => byId[id]?.fixed ? byId[id].key : byId[id] ? keyLabel(shortcut(id)) : id;
  window.hotkey = spec => {
    const parts = spec.toLowerCase().split('+'), k = parts.pop();
    const code = /^[a-z]$/.test(k) ? 'Key' + k.toUpperCase() : /^\d$/.test(k) ? 'Digit' + k : null;
    return e => MODS.every(m => !!e[m + 'Key'] === parts.includes(m))
      && ((e.key === ' ' ? 'space' : String(e.key).toLowerCase()) === k || !!code && e.code === code);
  };
  window.pressed = (e, id) => hotkey(shortcut(id))(e);
  window.keySpec = e => {
    const k = /^[a-z0-9]$/i.test(e.key) ? e.key.toLowerCase() : /^(Key[A-Z]|Digit\d)$/.test(e.code) ? e.code.slice(-1).toLowerCase()
      : e.key === ' ' ? 'space' : e.key === 'Enter' ? 'enter' : null;
    return k && MODS.filter(m => e[m + 'Key']).concat(k).join('+');
  };
  window.keyIds = mode => SHORTCUTS.filter(s => s.modes.includes(mode)).map(s => s.id);
  window.keysTip = ids => {
    const rows = ids.filter(id => byId[id]).map(id => [keyFor(id), byId[id].text]);
    const w = Math.max(0, ...rows.map(([k]) => k.length));
    return rows.map(([k, t]) => k.padEnd(w) + '  ' + t).join('\n');
  };
  window.infoButton = ids => `<button type="button" class="info" data-tip="shortcuts" data-keys="${esc(ids.join(' '))}" aria-label="keyboard shortcuts">${svg('info')}</button>`;

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

  window.cardForm = async (slug, card = {}, newSet = false) => {
    const url = '/api/cards/' + encodeURIComponent(slug);
    const t = document.createElement('template');
    const [topic, deck] = await Promise.all([api('/api/topic/' + encodeURIComponent(slug)).catch(() => ({})), api(url).catch(() => ({}))]);
    t.innerHTML = topic.html || '';
    const taken = (deck.sets || []).map(s => s.name);
    const sets = newSet ? (deck.notes || []).filter(n => !taken.includes(n))
      : [...new Set([...(deck.notes || []), ...taken])].filter(s => s !== 'unsorted');
    const notes = [...t.content.querySelectorAll('h1')].map(h => h.textContent.trim());
    const dlg = document.createElement('dialog');
    dlg.className = 'card-form float';
    dlg.innerHTML = `<form>
      <p class="frame-title">${newSet ? 'new card set · first card' : card.id ? 'edit card' : 'new card'}</p>
      <label>set<input name="set" list="card-sets" value="${esc(card.set === 'unsorted' ? '' : card.set || '')}" placeholder="a note title, or any name" autocomplete="off"></label>
      <datalist id="card-sets">${sets.map(n => `<option value="${esc(n)}">`).join('')}</datalist>
      <label>front (question)<textarea name="front" rows="2" placeholder="a question">${esc(card.front || '')}</textarea></label>
      <label>back (answer)<textarea name="back" rows="3" placeholder="the answer, one or two sentences">${esc(card.back || '')}</textarea></label>
      <label>note<input name="note" list="card-notes" value="${esc(card.note || '')}" placeholder="H1 of the note" autocomplete="off"></label>
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
        if (newSet && !f.set.trim()) return dlg.querySelector('[role=status]').textContent = '✕ name the set: a note without cards, or any name';
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
      form.elements[newSet ? 'set' : card.front ? 'back' : 'front'].focus();
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
        </div>
      </header>
      <div class="shell-body">
        <aside class="explorer"><div class="frame">
          <label class="frame-search"><svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><circle cx="7" cy="7" r="5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M11 11l3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><input id="tree-filter" type="search" placeholder="filter…" aria-label="Filter topics and notes" autocomplete="off" spellcheck="false"></label>
          <nav class="tree" id="tree"></nav>
        </div><div class="explorer-grip" id="explorer-grip" title="Drag to resize · double-click to reset"></div></aside>
        <main class="panel" id="app"></main>
      </div>
      <footer class="statusline">
        <button class="sl-side" id="side-toggle" title="Toggle sidebar" aria-label="Toggle sidebar"><svg viewBox="0 0 16 16" width="15" height="15" aria-hidden="true"><rect x="1.5" y="2.5" width="13" height="11" fill="none" stroke="currentColor" stroke-width="1.4"/><path d="M6 2.5v11" stroke="currentColor" stroke-width="1.4"/></svg></button>
        <span class="mode" id="mode">NORMAL</span>
        <span class="sl-path" id="path">~/topics</span>
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
          <span class="sl-ctl" title="Theme"><span aria-hidden="true">◐</span>${themeSelector()}</span>
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

    const store = (k, v) => { try { v === undefined ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} };
    const stored = k => { try { return localStorage.getItem(k); } catch { return null; } };
    const root = document.documentElement, grip = document.getElementById('explorer-grip');
    const setSide = w => w ? root.style.setProperty('--explorer-w', w + 'px') : root.style.removeProperty('--explorer-w');
    setSide(stored('explorer-w'));
    root.classList.toggle('explorer-hidden', stored('explorer-hidden') === '1');
    const toggle = document.getElementById('side-toggle');
    toggle.setAttribute('aria-pressed', !root.classList.contains('explorer-hidden'));
    toggle.onclick = () => {
      const hidden = root.classList.toggle('explorer-hidden');
      toggle.setAttribute('aria-pressed', !hidden);
      store('explorer-hidden', hidden ? '1' : undefined);
    };
    grip.onpointerdown = e => {
      grip.setPointerCapture(e.pointerId);
      root.classList.add('resizing');
      const x0 = e.clientX, w0 = grip.parentElement.getBoundingClientRect().width;
      grip.onpointermove = m => setSide(Math.round(Math.max(180, Math.min(innerWidth / 2, w0 + m.clientX - x0))));
      grip.onpointerup = () => {
        grip.onpointermove = grip.onpointerup = null;
        root.classList.remove('resizing');
        store('explorer-w', parseInt(root.style.getPropertyValue('--explorer-w')) || undefined);
      };
    };
    grip.ondblclick = () => { setSide(null); store('explorer-w'); };

    const params = new URLSearchParams(location.search);
    const topic = params.get('topic');
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

    const tools = document.getElementById('tools');
    tools.addEventListener('click', closeTip);
    tools.addEventListener('focusout', closeTip);
    ['mouseover', 'focusin'].forEach(type => tools.addEventListener(type, e => {
      const el = e.target.closest('[data-tip]');
      if (el) showTip(el);
    }));

    const bar = document.querySelector('.waybar');
    const fit = () => {
      bar.classList.remove('tight');
      bar.classList.toggle('tight', tools.scrollWidth > tools.clientWidth);
    };
    new ResizeObserver(fit).observe(bar);
    new MutationObserver(fit).observe(tools, { childList: true, subtree: true });

    const treeEl = document.getElementById('tree');
    const filter = document.getElementById('tree-filter');
    filter.addEventListener('input', () => {
      const q = filter.value.trim().toLowerCase();
      treeEl.querySelectorAll('details').forEach(d => {
        const sum = d.querySelector('summary');
        const own = (sum.textContent + ' ' + sum.title).toLowerCase().includes(q);
        let any = false;
        d.querySelectorAll('li').forEach(li => {
          const hit = !q || own || li.textContent.toLowerCase().includes(q);
          li.hidden = !hit;
          any ||= hit && !!q && !own;
        });
        d.hidden = !!q && !own && !any;
        d.open = q ? any || d.open && own : d.classList.contains('current');
      });
    });
    filter.addEventListener('keydown', e => {
      if (e.key === 'Escape') { filter.value = ''; filter.dispatchEvent(new Event('input')); filter.blur(); }
    });

    return {
      app,
      tree: treeEl,
      tools,
      path: t => document.getElementById('path').textContent = t,
      mode: (t, cls = '') => Object.assign(document.getElementById('mode'), { textContent: t, className: 'mode ' + cls }),
    };
  };
})();
