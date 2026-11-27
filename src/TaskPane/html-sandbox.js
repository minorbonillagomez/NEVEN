/**
 * html-sandbox.js - A-08 (SEC-07): politica unica de srcdoc para el HTML que producen
 * los motores (R, Julia, Python) y la IA. Todo sitio del TaskPane que inserte ese HTML
 * debe usar este modulo.
 *
 * Politica: iframe con sandbox="allow-scripts allow-downloads" y SIN allow-same-origin.
 * El documento queda en un origen opaco: no lee <meta name="neven-token">, no toca el
 * DOM, las cookies ni el storage de la pagina padre, y sus fetch al servidor local no
 * llevan X-NEVEN-Token (neven-auth.js solo parchea el fetch de la pagina padre).
 * allow-scripts permite los informes ACP y Plotly interactivos; allow-downloads permite
 * los botones de descarga CSV de esos informes.
 *
 * Exportar PNG/SVG de un grafico dentro del iframe se hace por postMessage: un pequeno
 * puente se anade al final del srcdoc y llama a Plotly.toImage dentro del aislamiento.
 */
(function (root) {
  'use strict';

  var SANDBOX = 'allow-scripts allow-downloads';

  var BRIDGE = '(function(){window.addEventListener("message",function(e){' +
    'if(e.source!==window.parent)return;var d=e.data;if(!d||d.neven!=="export")return;' +
    'function r(o){o.neven="export-result";o.id=d.id;window.parent.postMessage(o,"*");}' +
    'try{var g=document.querySelector(".js-plotly-plot");' +
    'if(!g||!window.Plotly){r({ok:false,reason:"el contenido no es un grafico Plotly exportable"});return;}' +
    'window.Plotly.toImage(g,{format:d.format,width:d.width||1200,height:d.height||600})' +
    '.then(function(u){r({ok:true,dataUrl:u});},' +
    'function(x){r({ok:false,reason:String(x&&x.message||x)});});' +
    '}catch(x){r({ok:false,reason:String(x&&x.message||x)});}});})();';

  function report(msg) {
    if (typeof root.showToast === 'function') { root.showToast(msg); return; }
    if (typeof root.alert === 'function') { root.alert(msg); }
  }

  function escapeAttr(s) {
    return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function withBridge(html) {
    return html + '\n<script>' + BRIDGE + '<\/script>';
  }

  /** Aplica la politica a un iframe existente. Informa al usuario si el HTML no es valido. */
  function applyTo(iframe, html) {
    // sandbox ANTES de srcdoc: el documento nunca se carga sin aislamiento.
    iframe.setAttribute('sandbox', SANDBOX);
    iframe.setAttribute('referrerpolicy', 'no-referrer');
    if (typeof html !== 'string' || html === '') {
      report('NEVEN: el motor no devolvio HTML para mostrar (contenido vacio o de tipo ' +
        (typeof html) + ').');
      iframe.setAttribute('srcdoc', '');
      return iframe;
    }
    iframe.setAttribute('srcdoc', withBridge(html));
    return iframe;
  }

  /** Crea un iframe nuevo con la politica aplicada. */
  function createFrame(html, opts) {
    var iframe = root.document.createElement('iframe');
    opts = opts || {};
    iframe.style.width = '100%';
    iframe.style.height = opts.height || '420px';
    iframe.style.border = 'none';
    if (opts.background) { iframe.style.background = opts.background; }
    return applyTo(iframe, html);
  }

  /** HTML de una ventana contenedora: solo un iframe aislado a pantalla completa. */
  function windowHtml(html, title) {
    return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>' +
      escapeAttr(title || 'NEVEN') + '</title></head>' +
      '<body style="margin:0"><iframe sandbox="' + SANDBOX + '" referrerpolicy="no-referrer" ' +
      'style="border:0;width:100vw;height:100vh" srcdoc="' + escapeAttr(withBridge(html)) +
      '"></iframe></body></html>';
  }

  /** Abre el HTML en una ventana nueva dentro de un iframe aislado. */
  function openInWindow(html, title, size) {
    if (typeof html !== 'string' || html === '') {
      report('NEVEN: no hay HTML para abrir en una ventana nueva.');
      return null;
    }
    var win = root.open('', '_blank', size || 'width=1000,height=700');
    if (!win) {
      report('NEVEN: el navegador bloqueo la ventana emergente; permita ventanas emergentes para este sitio.');
      return null;
    }
    win.document.write(windowHtml(html, title));
    win.document.close();
    return win;
  }

  /** Exporta el grafico Plotly del iframe como png/svg y lo descarga. Informa el motivo si falla. */
  function exportImage(iframe, name, format) {
    format = format || 'png';
    var id = 'exp-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    return new Promise(function (resolve) {
      var done = false;
      var timer;
      function finish(ok, reason) {
        if (done) { return; }
        done = true;
        root.clearTimeout(timer);
        root.removeEventListener('message', onMsg);
        if (!ok) { report('NEVEN: no se pudo exportar ' + format.toUpperCase() + ': ' + reason); }
        resolve(ok);
      }
      function onMsg(e) {
        var d = e.data;
        if (!iframe.contentWindow || e.source !== iframe.contentWindow) { return; }
        if (!d || d.neven !== 'export-result' || d.id !== id) { return; }
        if (!d.ok) { finish(false, d.reason || 'motivo desconocido'); return; }
        var a = root.document.createElement('a');
        a.href = d.dataUrl;
        a.download = String(name || 'neven-grafico').replace(/[^a-z0-9_-]/gi, '_') + '.' + format;
        root.document.body.appendChild(a);
        a.click();
        root.document.body.removeChild(a);
        finish(true);
      }
      root.addEventListener('message', onMsg);
      timer = root.setTimeout(function () {
        finish(false, 'el grafico no respondio (puede no ser Plotly o aun no haber cargado)');
      }, 8000);
      if (!iframe.contentWindow) { finish(false, 'el iframe no esta cargado'); return; }
      iframe.contentWindow.postMessage({ neven: 'export', id: id, format: format }, '*');
    });
  }

  var api = {
    SANDBOX: SANDBOX,
    applyTo: applyTo,
    createFrame: createFrame,
    openInWindow: openInWindow,
    exportImage: exportImage,
    windowHtml: windowHtml
  };
  root.NEVENHtmlSandbox = api;
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; }
})(typeof window !== 'undefined' ? window : globalThis);
