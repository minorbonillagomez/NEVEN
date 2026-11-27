// NEVEN - A-08 (SEC-07): politica unica de srcdoc. Carga src/TaskPane/html-sandbox.js en un
// contexto vm con un DOM simulado. Uso: node html_sandbox_check.js (codigo 0 = todo bien)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const SRC = fs.readFileSync(path.join(__dirname, '..', '..', 'TaskPane', 'html-sandbox.js'), 'utf8');

function makeEnv(opts) {
  opts = opts || {};
  const log = { toasts: [], opened: [], links: [], listeners: [], posted: [], attrOrder: [] };
  function makeIframe() {
    const attrs = {};
    return {
      tag: 'iframe', style: {}, attrs: attrs,
      setAttribute(k, v) { attrs[k] = v; log.attrOrder.push(k); },
      contentWindow: opts.noContentWindow ? null : { postMessage(m, o) { log.posted.push([m, o]); if (opts.onPost) opts.onPost(m); } }
    };
  }
  const sandbox = {
    document: {
      createElement(t) {
        if (t === 'iframe') return makeIframe();
        return { tag: t, href: '', download: '', click() { log.links.push(this); } };
      },
      body: { appendChild() {}, removeChild() {} }
    },
    showToast: (m) => log.toasts.push(m),
    addEventListener(t, fn) { log.listeners.push(fn); },
    removeEventListener(t, fn) { const i = log.listeners.indexOf(fn); if (i >= 0) log.listeners.splice(i, 1); },
    setTimeout: opts.fastTimeout ? (fn) => setTimeout(fn, 5) : setTimeout,
    clearTimeout: clearTimeout,
    open() {
      if (opts.popupBlocked) return null;
      const w = { html: '', document: { write(h) { w.html += h; }, close() { w.closed = true; } } };
      log.opened.push(w);
      return w;
    },
    Promise: Promise
  };
  sandbox.window = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox, { filename: 'html-sandbox.js' });
  return { api: sandbox.NEVENHtmlSandbox, log: log, iframe: makeIframe };
}

const ENGINE = '<html><body><script>fetch("/api/x",{headers:{"X-NEVEN-Token":parent.document.querySelector("meta").content}})</script><p>informe ACP</p></body></html>';

function caseSandboxPolicy() {
  const env = makeEnv();
  const f = env.api.createFrame(ENGINE);
  assert.strictEqual(f.attrs.sandbox, 'allow-scripts allow-downloads');
  assert.ok(f.attrs.sandbox.indexOf('allow-same-origin') < 0, 'allow-same-origin anula el aislamiento');
  assert.ok(f.attrs.sandbox.indexOf('allow-top-navigation') < 0);
  assert.ok(f.attrs.sandbox.indexOf('allow-popups') < 0);
  assert.ok(f.attrs.srcdoc.indexOf(ENGINE) === 0, 'el HTML del motor se conserva integro');
  assert.ok(env.log.attrOrder.indexOf('sandbox') < env.log.attrOrder.indexOf('srcdoc'), 'sandbox debe fijarse antes que srcdoc');
  assert.strictEqual(f.attrs.referrerpolicy, 'no-referrer');
  assert.strictEqual(f.attrs.src, undefined);
  console.log('ok  iframe con sandbox sin allow-same-origin, fijado antes de srcdoc');
}

function caseApplyToExisting() {
  const env = makeEnv();
  const f = env.iframe();
  env.api.applyTo(f, '<p>x</p>');
  assert.strictEqual(f.attrs.sandbox, env.api.SANDBOX);
  assert.ok(f.attrs.srcdoc.indexOf('<p>x</p>') === 0);
  console.log('ok  applyTo sobre un iframe existente aplica la misma politica');
}

function caseEmptyReported() {
  const env = makeEnv();
  const f = env.api.createFrame('');
  assert.strictEqual(f.attrs.sandbox, env.api.SANDBOX);
  assert.strictEqual(f.attrs.srcdoc, '');
  assert.ok(env.log.toasts.length === 1 && /no devolvio HTML/.test(env.log.toasts[0]), String(env.log.toasts));
  const env2 = makeEnv();
  env2.api.createFrame(undefined);
  assert.ok(env2.log.toasts.length === 1 && /undefined/.test(env2.log.toasts[0]));
  console.log('ok  HTML vacio o ausente: se informa el motivo');
}

function caseWindow() {
  const env = makeEnv();
  const w = env.api.openInWindow(ENGINE, 'Grafico <b>"x"</b>');
  assert.ok(w, 'ventana abierta');
  assert.ok(w.closed);
  assert.ok(/<iframe sandbox="allow-scripts allow-downloads"/.test(w.html), w.html.slice(0, 200));
  assert.ok(w.html.indexOf('allow-same-origin') < 0);
  assert.ok(w.html.indexOf('<script>fetch(') < 0, 'el script del motor no debe estar en claro en la ventana padre');
  assert.ok(w.html.indexOf('srcdoc="') > 0);
  assert.ok(w.html.indexOf('<title>Grafico &lt;b&gt;') > 0, 'titulo escapado');
  const outside = w.html.replace(/srcdoc="[^"]*"/, '');
  assert.ok(outside.indexOf('<script') < 0, 'la ventana contenedora no ejecuta scripts propios del motor');
  console.log('ok  ventana nueva: el HTML del motor va en iframe aislado, escapado');
}

function caseWindowBlockedAndEmpty() {
  const env = makeEnv({ popupBlocked: true });
  assert.strictEqual(env.api.openInWindow(ENGINE, 't'), null);
  assert.ok(env.log.toasts.length === 1 && /bloqueo la ventana emergente/.test(env.log.toasts[0]));
  const env2 = makeEnv();
  assert.strictEqual(env2.api.openInWindow('', 't'), null);
  assert.ok(/no hay HTML/.test(env2.log.toasts[0]));
  assert.strictEqual(env2.log.opened.length, 0);
  console.log('ok  ventana bloqueada o sin HTML: se informa el motivo');
}

// Ejecuta el puente del srcdoc en un contexto aparte, como lo haria el documento hijo.
function runBridge(srcdoc, withPlotly, plotlyFails) {
  const m = srcdoc.match(/<script>([\s\S]*)<\/script>\s*$/);
  assert.ok(m, 'el srcdoc debe llevar el puente al final');
  const sent = [];
  const parent = { postMessage(d, o) { sent.push([d, o]); } };
  let handler;
  const child = {
    addEventListener(t, fn) { handler = fn; },
    parent: parent,
    document: { querySelector: (s) => (withPlotly && s === '.js-plotly-plot') ? { id: 'gd' } : null },
    Plotly: withPlotly ? { toImage: () => plotlyFails ? Promise.reject(new Error('fallo toImage')) : Promise.resolve('data:image/png;base64,AAA') } : undefined
  };
  child.window = child;
  vm.createContext(child);
  vm.runInContext(m[1], child);
  return { send: (data, source) => handler({ source: source, data: data }), sent: sent, parent: parent };
}

async function caseBridge() {
  const env = makeEnv();
  const f = env.api.createFrame('<div class="js-plotly-plot"></div>');
  let b = runBridge(f.attrs.srcdoc, true, false);
  b.send({ neven: 'export', id: '1', format: 'png' }, {});
  assert.strictEqual(b.sent.length, 0, 'ignora mensajes que no vienen del padre');
  b.send({ neven: 'otro' }, b.parent);
  assert.strictEqual(b.sent.length, 0);
  b.send({ neven: 'export', id: '1', format: 'png' }, b.parent);
  await new Promise(r => setImmediate(r));
  assert.deepStrictEqual(JSON.parse(JSON.stringify(b.sent[0][0])), { neven: 'export-result', id: '1', ok: true, dataUrl: 'data:image/png;base64,AAA' });
  b = runBridge(f.attrs.srcdoc, false, false);
  b.send({ neven: 'export', id: '2', format: 'svg' }, b.parent);
  assert.strictEqual(b.sent[0][0].ok, false);
  assert.ok(/Plotly/.test(b.sent[0][0].reason));
  b = runBridge(f.attrs.srcdoc, true, true);
  b.send({ neven: 'export', id: '3', format: 'png' }, b.parent);
  await new Promise(r => setImmediate(r));
  assert.ok(b.sent[0][0].ok === false && /fallo toImage/.test(b.sent[0][0].reason));
  console.log('ok  puente de exportacion: responde solo al padre, informa motivos');
}

async function caseExport() {
  for (const fmt of ['png', 'svg']) {
    let ifr;
    const env = makeEnv({ onPost(m) {
      setImmediate(() => env.log.listeners.slice().forEach(fn => fn({ source: ifr.contentWindow, data: { neven: 'export-result', id: m.id, ok: true, dataUrl: 'data:image/' + fmt + ';base64,AA' } })));
    } });
    ifr = env.iframe();
    const ok = await env.api.exportImage(ifr, 'Mi grafico!', fmt);
    assert.strictEqual(ok, true);
    assert.strictEqual(env.log.links.length, 1);
    assert.strictEqual(env.log.links[0].download, 'Mi_grafico_.' + fmt);
    assert.ok(env.log.links[0].href.indexOf('data:image/' + fmt) === 0);
    assert.strictEqual(env.log.listeners.length, 0, 'listener retirado');
  }
  // un mensaje de otra ventana no cuenta
  let env = makeEnv({ fastTimeout: true, onPost(m) {
    setImmediate(() => env.log.listeners.slice().forEach(fn => fn({ source: {}, data: { neven: 'export-result', id: m.id, ok: true, dataUrl: 'data:x' } })));
  } });
  assert.strictEqual(await env.api.exportImage(env.iframe(), 'g', 'png'), false);
  assert.strictEqual(env.log.links.length, 0);
  assert.ok(/no respondio/.test(env.log.toasts[0]), String(env.log.toasts));
  // fallo informado por el hijo
  let ifr3;
  env = makeEnv({ onPost(m) {
    setImmediate(() => env.log.listeners.slice().forEach(fn => fn({ source: ifr3.contentWindow, data: { neven: 'export-result', id: m.id, ok: false, reason: 'el contenido no es un grafico Plotly exportable' } })));
  } });
  ifr3 = env.iframe();
  assert.strictEqual(await env.api.exportImage(ifr3, 'g', 'png'), false);
  assert.ok(/no se pudo exportar PNG: el contenido no es un grafico Plotly/.test(env.log.toasts[0]), String(env.log.toasts));
  // iframe no cargado
  env = makeEnv({ noContentWindow: true });
  assert.strictEqual(await env.api.exportImage(env.iframe(), 'g', 'svg'), false);
  assert.ok(/no se pudo exportar SVG: el iframe no esta cargado/.test(env.log.toasts[0]));
  console.log('ok  exportar PNG/SVG: descarga en exito, motivo en fallo');
}

(async () => {
  caseSandboxPolicy();
  caseApplyToExisting();
  caseEmptyReported();
  caseWindow();
  caseWindowBlockedAndEmpty();
  await caseBridge();
  await caseExport();
  console.log('todos los casos pasaron');
})().catch(e => { console.error('FALLO:', e && e.stack || e); process.exit(1); });
