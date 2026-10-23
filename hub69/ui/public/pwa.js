// Register only in an approved HTTPS/loopback mount. File review stays inert.
(() => {
  if (!window.isSecureContext || !('serviceWorker' in navigator) || location.protocol === 'file:') return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js', {scope: './'}).catch(() => {
      // Network UI remains usable if installation is unavailable.
    });
  });
})();
