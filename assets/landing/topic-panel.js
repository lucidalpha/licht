(() => {
  const panel = document.querySelector('#topic-panel');
  const links = [...document.querySelectorAll('.topic-link')];
  if (!panel || !links.length) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let activeLink;
  let revision = 0;
  let fade;
  const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

  links.forEach(link => {
    link.setAttribute('aria-controls', panel.id);
    link.setAttribute('aria-expanded', 'false');
    link.addEventListener('click', event => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (activeLink === link && panel.classList.contains('is-open')) close();
      else open(link);
    });
  });

  async function open(link) {
    const current = ++revision;
    fade?.cancel();
    const wasOpen = panel.classList.contains('is-open');
    activeLink = link;
    links.forEach(item => item.setAttribute('aria-expanded', String(item === link)));
    panel.setAttribute('aria-label', 'Leerer Bereich für ' + link.textContent);
    panel.hidden = false;
    panel.inert = false;
    panel.getBoundingClientRect();
    if (!motion.matches) await new Promise(resolve => {
      requestAnimationFrame(resolve);
      setTimeout(resolve, 50);
    });
    if (current !== revision) return;
    panel.classList.add('is-open');
    if (wasOpen && !motion.matches && panel.animate) {
      fade = panel.querySelector('.topic-blank').animate([{ opacity: 1 }, { opacity: .25 }, { opacity: 1 }], { duration: 400, easing: 'ease-in-out' });
    }
    if (!motion.matches) await pause(420);
    if (current !== revision) return;
    panel.scrollIntoView({ behavior: motion.matches ? 'instant' : 'smooth', block: 'nearest' });
  }

  async function close() {
    const current = ++revision;
    fade?.cancel();
    links.forEach(link => link.setAttribute('aria-expanded', 'false'));
    panel.inert = true;
    panel.classList.remove('is-open');
    activeLink?.focus({ preventScroll: true });
    activeLink = undefined;
    if (!motion.matches) await pause(420);
    if (current === revision) panel.hidden = true;
  }

  document.querySelector('.topics-section').addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      event.preventDefault();
      close();
    }
  });
})();
