(() => {
  const panel = document.querySelector('#topic-panel');
  const cards = [...document.querySelectorAll('.topic-card')];
  if (!panel || !cards.length || !window.fetch) return;
  const heading = panel.querySelector('#topic-panel-title');
  const content = panel.querySelector('.topic-panel-content');
  const closeButton = panel.querySelector('.topic-panel-close');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const cache = new Map();
  let revision = 0;
  let controller;
  let activeCard;
  let fade;
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
  const clearBusy = () => cards.forEach(card => card.removeAttribute('aria-busy'));

  cards.forEach(card => {
    card.setAttribute('aria-controls', panel.id);
    card.setAttribute('aria-expanded', 'false');
    card.querySelector('.topic-arrow').textContent = '↓';
    card.addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      open(card);
    });
  });

  async function open(card) {
    const current = ++revision;
    controller?.abort();
    fade?.cancel();
    clearBusy();
    controller = new AbortController();
    const url = card.href;
    card.setAttribute('aria-busy', 'true');
    try {
      if (!cache.has(url)) {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) throw new Error('Topic unavailable');
        const document = new DOMParser().parseFromString(await response.text(), 'text/html');
        const article = document.querySelector('.topic-content article');
        const title = article?.querySelector('h1');
        if (!article || !title) throw new Error('Topic missing');
        const label = title.textContent;
        article.querySelectorAll('.back-link, h1, script').forEach(node => node.remove());
        cache.set(url, { title: label, html: article.innerHTML });
      }
      if (current !== revision) return;
      const topic = cache.get(url);
      if (panel.classList.contains('is-open') && !motion.matches && content.animate) {
        fade = content.animate([{ opacity: 1, transform: 'translateY(0)' }, { opacity: 0, transform: 'translateY(-6px)' }], { duration: 140, fill: 'forwards', easing: 'ease' });
        await fade.finished.catch(() => {});
      }
      if (current !== revision) return;
      fade?.cancel();
      heading.textContent = topic.title;
      content.innerHTML = topic.html;
      activeCard = card;
      cards.forEach(item => item.setAttribute('aria-expanded', String(item === card)));
      clearBusy();
      panel.hidden = false;
      panel.inert = false;
      // Establish the collapsed frame before the expansion starts.
      panel.getBoundingClientRect();
      await new Promise(resolve => requestAnimationFrame(resolve));
      if (current !== revision) return;
      panel.classList.add('is-open');
      if (!motion.matches && content.animate) {
        fade = content.animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 320, easing: 'ease-out' });
      }
      if (!motion.matches) await pause(420);
      if (current !== revision) return;
      heading.focus({ preventScroll: true });
      panel.scrollIntoView({ behavior: motion.matches ? 'instant' : 'smooth', block: 'nearest' });
    } catch (error) {
      if (error.name !== 'AbortError' && current === revision) window.location.assign(url);
    } finally {
      if (current === revision) clearBusy();
    }
  }

  async function close() {
    const current = ++revision;
    controller?.abort();
    fade?.cancel();
    clearBusy();
    cards.forEach(card => card.setAttribute('aria-expanded', 'false'));
    panel.inert = true;
    panel.classList.remove('is-open');
    activeCard?.focus();
    if (!motion.matches) await pause(420);
    if (current === revision) panel.hidden = true;
  }

  closeButton.addEventListener('click', close);
  document.querySelector('.topics-section').addEventListener('keydown', event => {
    if (event.key === 'Escape' && (!panel.hidden || cards.some(card => card.hasAttribute('aria-busy')))) {
      event.preventDefault();
      close();
    }
  });
})();
