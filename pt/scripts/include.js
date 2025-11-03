async function loadIncludes() {
  const containers = document.querySelectorAll('[data-include]');
  for (const container of containers) {
    const name = container.dataset.include;
    if (!name) continue;

    const url = new URL(`../partials/${name}.html`, import.meta.url);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Falha ao carregar ${name}`);
      const html = await response.text();
      container.innerHTML = html;

      if (name === 'header') {
        applyLanguageSwitcher(container);
        applyNavigationLinks(container);
        setupMenuToggles(container);
      } else if (name === 'footer') {
        applyNavigationLinks(container);
      }
    } catch (error) {
      console.error(error);
      container.innerHTML = '';
    }
  }
}

function applyLanguageSwitcher(container) {
  const current = container.dataset.currentLang || document.body.dataset.lang || 'pt';
  let ptUrl = container.dataset.ptUrl || document.body.dataset.langPt || '#';
  let enUrl = container.dataset.enUrl || document.body.dataset.langEn || '#';
  const ptLink = container.querySelector('.language-option-pt');
  const enLink = container.querySelector('.language-option-en');
  const syncQuery = container.dataset.syncQuery === 'true';
  const query = window.location.search;

  if (syncQuery && query && query !== '?') {
    const appendQuery = (url) => {
      if (!url || url === '#') return url;
      return url.includes('?') ? `${url}&${query.slice(1)}` : `${url}${query}`;
    };
    ptUrl = appendQuery(ptUrl);
    enUrl = appendQuery(enUrl);
  }

  const normalizeLangUrl = (url) => {
    if (!url || url === '#') return url;
    if (/^(https?:|mailto:|tel:|\/)/i.test(url)) return url;
    try {
      const absolute = new URL(url, `${window.location.origin}/`);
      return `${absolute.pathname}${absolute.search}${absolute.hash}`;
    } catch {
      return url;
    }
  };

  if (current === 'pt') {
    enUrl = normalizeLangUrl(enUrl);
  } else if (current === 'en') {
    ptUrl = normalizeLangUrl(ptUrl);
  } else {
    ptUrl = normalizeLangUrl(ptUrl);
    enUrl = normalizeLangUrl(enUrl);
  }

  if (ptLink) {
    ptLink.href = ptUrl;
    ptLink.classList.toggle('current', current === 'pt');
  }
  if (enLink) {
    enLink.href = enUrl;
    enLink.classList.toggle('current', current === 'en');
  }
}

function setupMenuToggles(root = document) {
  root.querySelectorAll('.menu-toggle').forEach(button => {
    button.addEventListener('click', () => {
      const expanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!expanded));
      const submenu = button.nextElementSibling;
      if (submenu) submenu.classList.toggle('open', !expanded);
    });
  });
}

function applyNavigationLinks(container) {
  const prefix = container.dataset.linkPrefix || '';
  const currentLang = document.body.dataset.lang || container.dataset.currentLang || 'pt';
  container.querySelectorAll('[data-link]').forEach(anchor => {
    const target = anchor.dataset.link;
    if (!target) return;

    if (/^(https?:|mailto:|tel:|#)/i.test(target)) {
      anchor.setAttribute('href', target);
      return;
    }

    let resolved;
    if (prefix) {
      resolved = prefix.endsWith('/') ? `${prefix}${target}` : `${prefix}/${target}`;
    } else if (target.startsWith('../') || target.startsWith('./') || target.startsWith('/')) {
      resolved = target;
    } else {
      const langSegment = (currentLang || 'pt').replace(/[^a-z-]/gi, '') || 'pt';
      const langToken = `/${langSegment}/`;
      const path = window.location?.pathname || '';
      const langIndex = path.indexOf(langToken);
      const basePath = langIndex >= 0 ? path.slice(0, langIndex + langToken.length) : langToken;
      resolved = `${basePath}${target}`.replace(/\/{2,}/g, '/');
    }

    anchor.setAttribute('href', resolved);
  });
}

document.addEventListener('DOMContentLoaded', loadIncludes);
