(() => {
  let mermaidLoad, katexLoad, seq = 0;

  const isDark = () => getComputedStyle(document.documentElement).colorScheme !== 'light';

  const script = src => new Promise((ok, fail) => {
    const js = document.createElement('script');
    js.src = src;
    js.onload = ok;
    js.onerror = () => fail(new Error('could not load ' + src));
    document.head.appendChild(js);
  });

  const loadMermaid = () => (mermaidLoad ||= script('/app/vendor/mermaid.min.js').then(() => window.mermaid));

  const loadKatex = () => (katexLoad ||= (() => {
    const css = document.createElement('link');
    css.rel = 'stylesheet';
    css.href = '/app/vendor/katex/katex.min.css';
    document.head.appendChild(css);
    return script('/app/vendor/katex/katex.min.js').then(() => window.katex);
  })());

  const token = name => getComputedStyle(document.documentElement)
    .getPropertyValue(name).trim();

  const mermaidTheme = () => ({
    startOnLoad: false,
    securityLevel: 'strict',
    theme: 'base',
    themeVariables: {
      darkMode: isDark(),
      fontFamily: token('--mono') || 'ui-monospace, monospace',
      fontSize: token('--text-body') || '14px',
      background: token('--color-void'),
      mainBkg: token('--color-graphite'),
      primaryColor: token('--color-graphite'),
      primaryTextColor: token('--color-paper'),
      primaryBorderColor: token('--color-slate'),
      secondaryColor: token('--color-carbon'),
      tertiaryColor: token('--color-carbon'),
      lineColor: token('--color-pewter'),
      textColor: token('--color-paper'),
      noteBkgColor: token('--color-carbon'),
      noteTextColor: token('--color-fog'),
      noteBorderColor: token('--color-iron'),
    },
  });

  const escape = s => String(s).replace(/[<>&]/g,
    c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));

  const block = (kind, source) =>
    `<figure class="viz" data-kind="${kind === 'math' ? 'math' : 'mermaid'}" contenteditable="false">`
    + `<pre class="src">${escape(source)}</pre><div class="view"></div></figure>`;

  async function paint(fig) {
    const source = fig.querySelector('.src')?.textContent ?? '';
    const view = fig.querySelector('.view');
    if (!view) return;
    delete fig.dataset.error;
    if (!source.trim()) {
      view.replaceChildren();
      fig.classList.remove('painted');
      return;
    }
    const id = 'viz-' + (++seq);
    try {
      if (fig.dataset.kind === 'math') {
        const katex = await loadKatex();
        katex.render(source, view, { displayMode: true, throwOnError: true });
      } else {
        const mermaid = await loadMermaid();
        mermaid.initialize(mermaidTheme());
        const { svg } = await mermaid.render(id, source);
        view.innerHTML = svg;
      }
      fig.classList.add('painted');
    } catch (e) {
      document.getElementById('d' + id)?.remove();
      view.replaceChildren();
      fig.classList.remove('painted');
      fig.dataset.error = String(e?.message || e).split('\n')[0].slice(0, 200);
    }
  }

  const paintAll = (root = document) => {
    const found = [...root.querySelectorAll('figure.viz')];
    if (root.matches?.('figure.viz')) found.unshift(root);
    return Promise.all(found.map(paint));
  };

  function withBlocks(text) {
    const re = /```(mermaid|math)[ \t]*\r?\n([\s\S]*?)\r?\n?```[ \t]*(?:\n|$)/g;
    const out = [];
    let at = 0, m;
    while ((m = re.exec(text))) {
      out.push(escape(text.slice(at, m.index)), block(m[1], m[2]));
      at = re.lastIndex;
    }
    out.push(escape(text.slice(at)));
    return out.join('');
  }

  new MutationObserver(() => paintAll())
    .observe(document.documentElement, { attributeFilter: ['data-theme'] });

  Object.assign(window, { vizPaint: paintAll, vizBlock: block, vizText: withBlocks });
})();
