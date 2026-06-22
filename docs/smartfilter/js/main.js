// SmartFilter site — light progressive enhancement, no dependencies.

// Current year in the footer.
var yearEl = document.getElementById('year');
if (yearEl) { yearEl.textContent = new Date().getFullYear(); }

// Dismissible top download banner.
// On iOS Safari, Apple's native Smart App Banner takes over, so hide ours there
// to avoid showing two banners.
(function () {
  var banner = document.getElementById('appbanner');
  if (!banner) { return; }

  var isIOSSafari =
    /iP(hone|od|ad)/.test(navigator.platform || navigator.userAgent) &&
    /Safari/.test(navigator.userAgent) &&
    !/CriOS|FxiOS|EdgiOS/.test(navigator.userAgent);

  var dismissed = false;
  try { dismissed = localStorage.getItem('sf_banner_dismissed') === '1'; } catch (e) {}

  if (isIOSSafari || dismissed) {
    banner.classList.add('is-hidden');
  }

  var close = document.getElementById('appbanner-close');
  if (close) {
    close.addEventListener('click', function () {
      banner.classList.add('is-hidden');
      try { localStorage.setItem('sf_banner_dismissed', '1'); } catch (e) {}
    });
  }
})();
