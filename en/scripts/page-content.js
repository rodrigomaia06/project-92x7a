const DEFAULT_MESSAGES = {
  en: {
    error: 'Unable to load the content. Please try again later.',
  },
  pt: {
    error: 'Não foi possível carregar o conteúdo. Tenta novamente mais tarde.',
  },
};

function parseFrontMatter(raw) {
  if (raw.startsWith('---')) {
    const end = raw.indexOf('\n---', 3);
    if (end !== -1) {
      const metaBlock = raw.slice(3, end).trim();
      const body = raw.slice(end + 4).replace(/^\s+/, '');
      const meta = {};
      metaBlock.split(/\r?\n/).forEach((line) => {
        const [key, ...rest] = line.split(':');
        if (!key || !rest.length) return;
        meta[key.trim()] = rest.join(':').trim();
      });
      return { meta, body };
    }
  }
  return { meta: {}, body: raw };
}

function applyMetadata(meta) {
  if (!meta) return;
  const heading = meta.heading || meta.title;
  if (heading) {
    const headingEl = document.querySelector('.page-header h1');
    if (headingEl) headingEl.textContent = heading;
    if (meta.title) document.title = `${meta.title} | Matilde Batalha`;
  }
  if (meta.description) {
    const metaDescription =
      document.querySelector('meta[name="description"]') ||
      (() => {
        const el = document.createElement('meta');
        el.setAttribute('name', 'description');
        document.head.appendChild(el);
        return el;
      })();
    metaDescription.setAttribute('content', meta.description);
  }
}

function enhanceContent(container) {
  container.querySelectorAll('img').forEach((img) => {
    if (!img.hasAttribute('loading')) {
      img.setAttribute('loading', 'lazy');
    }
    const alt = img.getAttribute('alt');
    if (!alt || !alt.trim()) {
      img.setAttribute('alt', '');
    }
  });

  container.querySelectorAll('a[href^="http"]').forEach((link) => {
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'noopener');
  });
}

async function loadMarkdown(container) {
  const src = container.dataset.contentSrc;
  if (!src) return;

  const lang = document.body.dataset.lang || 'en';
  const messages = DEFAULT_MESSAGES[lang] || DEFAULT_MESSAGES.en;

  try {
    const response = await fetch(src, { cache: 'no-store' });
    if (!response.ok) throw new Error(`Failed to load ${src}`);
    const raw = await response.text();
    const { meta, body } = parseFrontMatter(raw);
    const trimmed = body.trim();
    if (!trimmed) {
      container.innerHTML = '';
      return;
    }

    if (!window.marked) {
      container.textContent = trimmed;
      return;
    }

    const html = window.marked.parse(trimmed, { async: false, mangle: false, headerIds: false });
    const safeHtml = window.DOMPurify ? window.DOMPurify.sanitize(html) : html;
    container.innerHTML = safeHtml;

    applyMetadata(meta);
    enhanceContent(container);
  } catch (error) {
    console.error(error);
    container.innerHTML = `<p class="error-message">${messages.error}</p>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.page-content[data-content-src]').forEach((container) => {
    loadMarkdown(container);
  });
});
