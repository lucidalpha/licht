(() => {
  const elements = [...document.querySelectorAll('[data-reveal]')];
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (motion.matches || !('IntersectionObserver' in window)) return;

  let observer;
  let frame = null;
  const stopScrollCheck = () => {
    window.removeEventListener('scroll', onScroll);
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
  };
  const finishIfComplete = () => {
    if (elements.every(element => element.classList.contains('is-visible'))) {
      observer?.disconnect();
      stopScrollCheck();
    }
  };
  const reveal = element => {
    element.classList.add('is-visible');
    observer?.unobserve(element);
  };
  const onScroll = () => {
    if (frame !== null) return;
    frame = requestAnimationFrame(() => {
      frame = null;
      elements.forEach(element => {
        if (!element.classList.contains('is-visible') &&
            element.getBoundingClientRect().top < window.innerHeight - 36) reveal(element);
      });
      finishIfComplete();
    });
  };
  const showAll = () => {
    elements.forEach(element => element.classList.add('is-visible'));
    observer?.disconnect();
    stopScrollCheck();
  };

  try {
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        reveal(entry.target);
      });
      finishIfComplete();
    }, { threshold: 0.12, rootMargin: '0px 0px -36px 0px' });

    elements.forEach(element => {
      if (element.getBoundingClientRect().top < window.innerHeight) {
        element.classList.add('is-visible');
        return;
      }
      element.classList.add('reveal-ready');
      observer.observe(element);
    });

    window.addEventListener('scroll', onScroll, { passive: true });
    finishIfComplete();

    const onMotionChange = event => { if (event.matches) showAll(); };
    if (motion.addEventListener) motion.addEventListener('change', onMotionChange);
    else motion.addListener(onMotionChange);
  } catch {
    showAll();
  }
})();
