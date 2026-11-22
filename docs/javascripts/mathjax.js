// MathJax for two kinds of page:
// - Markdown pages: pymdownx.arithmatex wraps math in class "arithmatex" with \( \) and \[ \].
// - Notebook pages (mkdocs-jupyter): markdown cells keep Jupyter's $...$ and $$...$$ in
//   plain <p>, <li> and <td> elements inside class "jp-RenderedMarkdown".
// MathJax ignores every element (even one with no class) unless its own class matches
// processHtmlClass, so a "$" in ordinary text or code is never turned into math. The
// elements of notebook markdown cells are therefore tagged "jp-math" before typesetting.
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"], ["$", "$"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex|jp-math",
  },
};

document$.subscribe(() => {
  document
    .querySelectorAll(".jp-RenderedMarkdown, .jp-RenderedMarkdown *:not([class])")
    .forEach((el) => el.classList.add("jp-math"));
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
