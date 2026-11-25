/**
 * neven-auth.js - adds the per-session secret (SEC-01) to every request the
 * TaskPane sends to the local NEVEN server, and reports rejections visibly.
 * The server injects the secret as <meta name="neven-token"> into the HTML it
 * serves. Must be loaded before any script that calls fetch().
 */
(function () {
  'use strict';
  var HEADER = 'X-NEVEN-Token';
  var origFetch = window.fetch;

  function token() {
    var m = document.querySelector('meta[name="neven-token"]');
    return m ? m.getAttribute('content') : '';
  }

  function isLocalApi(url) {
    try {
      var u = new URL(url, window.location.href);
      return u.origin === window.location.origin;
    } catch (e) { return false; }
  }

  function notify(msg) {
    if (typeof window.showToast === 'function') { window.showToast(msg); return; }
    var d = document.createElement('div');
    d.textContent = msg;
    d.style.cssText = 'position:fixed;bottom:40px;left:50%;transform:translateX(-50%);' +
      'background:#7a1f1f;color:#fff;padding:8px 18px;border-radius:6px;z-index:9999;font-size:12px';
    (document.body || document.documentElement).appendChild(d);
    setTimeout(function () { if (d.parentNode) d.parentNode.removeChild(d); }, 8000);
  }

  window.fetch = function (input, init) {
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    if (!isLocalApi(url)) { return origFetch.apply(this, arguments); }
    init = init || {};
    var headers = new Headers(init.headers || (typeof input !== 'string' && input.headers) || {});
    var tok = token();
    if (tok) { headers.set(HEADER, tok); }
    init.headers = headers;
    return origFetch.call(this, input, init).then(function (resp) {
      if (resp.status === 401 || resp.status === 403) {
        var why = resp.status === 401
          ? 'NEVEN: peticion rechazada por el servidor local (falta el secreto de sesion). Recargue NEVEN Studio.'
          : 'NEVEN: peticion rechazada por el servidor local (origen o ruta no permitidos).';
        notify(why);
      }
      return resp;
    });
  };
})();