// Apply the stored or system theme before first paint (mirrors src/theme/theme.ts).
(function () {
  var stored = null;
  try { stored = localStorage.getItem('medrag-theme'); } catch (e) {}
  var dark = stored === 'dark' || (stored !== 'light' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  if (dark) document.documentElement.classList.add('dark');
})();
