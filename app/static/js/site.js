document.addEventListener("DOMContentLoaded", () => {
  const animatedSelectors = [
    ".hero-wrap",
    ".card",
    "section h1",
    "section h2",
    ".table-responsive",
    "form",
  ];

  const animatedNodes = document.querySelectorAll(animatedSelectors.join(","));
  animatedNodes.forEach((node, index) => {
    node.classList.add("reveal");
    node.style.transitionDelay = `${(index % 6) * 45}ms`;
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: "0px 0px -30px 0px",
    }
  );

  animatedNodes.forEach((node) => observer.observe(node));
});
