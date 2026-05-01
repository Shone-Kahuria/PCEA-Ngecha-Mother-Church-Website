document.addEventListener("DOMContentLoaded", () => {
  const nav = document.getElementById("siteNav");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const setNavState = () => {
    if (!nav) {
      return;
    }
    nav.classList.toggle("is-scrolled", window.scrollY > 24);
  };

  setNavState();
  window.addEventListener("scroll", setNavState, { passive: true });

  const animatedSelectors = [
    ".hero-wrap",
    ".page-header",
    ".card",
    ".table-responsive",
    ".module-chip",
    "section h1",
    "section h2",
    "form",
  ];

  const animatedNodes = document.querySelectorAll(animatedSelectors.join(","));
  if (reduceMotion) {
    animatedNodes.forEach((node) => node.classList.add("in-view"));
    return;
  }

  animatedNodes.forEach((node, index) => {
    node.classList.add("reveal");
    node.style.transitionDelay = `${(index % 7) * 45}ms`;
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) {
          return;
        }
        entry.target.classList.add("in-view");
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.12,
      rootMargin: "0px 0px -45px 0px",
    }
  );

  animatedNodes.forEach((node) => observer.observe(node));
});
