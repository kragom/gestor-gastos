window.Balance = (function () {
  function applyTheme(theme) {
    const dark = theme === 'dark' || (theme === 'system' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', dark);
    document.documentElement.setAttribute('data-theme', theme);
  }
  function setTheme(theme) {
    localStorage.setItem('balance-theme', theme);
    applyTheme(theme);
    // Notifica al servidor (best effort) para persistir la preferencia
    const fd = new FormData(); fd.append('tema', theme);
    fetch('/ajustes/tema', { method: 'POST', body: fd }).catch(() => {});
  }
  function cycleTheme() {
    const cur = localStorage.getItem('balance-theme') || 'system';
    const next = cur === 'light' ? 'dark' : cur === 'dark' ? 'system' : 'light';
    setTheme(next);
  }

  // Donut chart reutilizable
  function donut(canvasId, labels, data, colors) {
    const el = document.getElementById(canvasId);
    if (!el || typeof Chart === 'undefined') return;
    new Chart(el, {
      type: 'doughnut',
      data: { labels, datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 6 }] },
      options: {
        cutout: '68%', responsive: true, maintainAspectRatio: true,
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
      },
    });
  }

  function bars(canvasId, labels, series) {
    const el = document.getElementById(canvasId);
    if (!el || typeof Chart === 'undefined') return;
    new Chart(el, {
      type: 'bar',
      data: { labels, datasets: series },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { x: { grid: { display: false } }, y: { beginAtZero: true } },
      },
    });
  }

  // Sincroniza el tema del sistema si está en 'system'
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const cur = localStorage.getItem('balance-theme') || 'system';
    if (cur === 'system') applyTheme('system');
  });

  // Registro del service worker (PWA)
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch(() => {});
    });
  }

  return { setTheme, cycleTheme, donut, bars, applyTheme };
})();
