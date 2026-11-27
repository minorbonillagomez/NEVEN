// NEVEN - A-03: el boton DESCARGAR del TaskPane no debe navegar la pagina.
// Carga src/TaskPane/audiobook.js en un contexto vm con un DOM simulado y comprueba que
// la descarga usa fetch (con X-NEVEN-Token) + Blob + enlace blob:, sin tocar location.
// Uso: node audiobook_download_check.js   (codigo 0 = todo bien)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const SRC = fs.readFileSync(path.join(__dirname, '..', '..', 'TaskPane', 'audiobook.js'), 'utf8');

function makeEnv(fetchImpl) {
  const log = { fetches: [], links: [], toasts: [], locationWrites: [], revokes: [], timers: [] };
  const elements = {};
  function element(id) {
    if (!elements[id]) {
      elements[id] = new Proxy({ id: id }, {
        get(t, k) {
          if (k in t) return t[k];
          if (typeof k === 'symbol') return undefined;
          if (k === 'style') return (t.style = {});
          if (k === 'classList') return { add() {}, remove() {}, toggle() {}, contains() { return false; } };
          return function () {};
        }
      });
    }
    return elements[id];
  }
  const locationGuard = new Proxy({}, {
    set(t, k, v) { log.locationWrites.push([k, v]); throw new Error('navegacion no permitida: location.' + String(k)); },
    get() { return 'https://localhost:5555/taskpane.html'; }
  });
  const documentMock = {
    readyState: 'loading',            // evita el auto-init: solo se registra el listener
    addEventListener() {},
    getElementById: element,
    querySelector(sel) {
      if (sel === 'meta[name="neven-token"]') return { getAttribute: () => 'TOKEN-DE-PRUEBA' };
      return null;
    },
    createElement(tag) {
      const el = { tag: tag, href: '', download: '', clicks: 0, click() { this.clicks++; } };
      if (tag === 'a') log.links.push(el);
      return el;
    },
    body: { appendChild() {}, removeChild() {} }
  };
  const sandbox = {
    console: { log() {}, warn() {}, error() {} },
    document: documentMock,
    location: locationGuard,
    Headers: Headers,
    Blob: Blob,
    URL: {
      createObjectURL(b) { assert.ok(b instanceof Blob); return 'blob:test-' + b.size; },
      revokeObjectURL(u) { log.revokes.push(u); }
    },
    setTimeout(fn, ms) { log.timers.push(ms); return 1; },
    setInterval() { return 1; },
    clearInterval() {},
    fetch(url, init) {
      log.fetches.push({ url: url, token: new Headers((init && init.headers) || {}).get('X-NEVEN-Token') });
      return fetchImpl(url);
    }
  };
  sandbox.window = sandbox;
  sandbox.window.showToast = (m) => log.toasts.push(m);
  vm.createContext(sandbox);
  vm.runInContext(SRC, sandbox, { filename: 'audiobook.js' });
  return { api: sandbox.NEVENAudiobook, log: log, button: element('btn-audiobook-download-m4b') };
}

const RESULT = { output_path: 'C:\\out\\Libro \u00e1 \u00e9.m4b', title: 'T', author: 'A', chapters: 2, duration: 10 };

async function caseOk() {
  const env = makeEnv(async () => ({ ok: true, status: 200, blob: async () => new Blob(['audio-bytes']) }));
  env.api.showResult(Object.assign({}, RESULT));
  await env.api.downloadM4B();
  const l = env.log;
  assert.strictEqual(l.fetches.length, 1, 'un solo fetch');
  assert.strictEqual(l.fetches[0].url, 'http://localhost:5557/api/download/Libro%20%C3%A1%20%C3%A9.m4b');
  assert.strictEqual(l.fetches[0].token, 'TOKEN-DE-PRUEBA', 'el fetch lleva X-NEVEN-Token');
  assert.strictEqual(l.links.length, 1, 'un enlace');
  assert.ok(l.links[0].href.startsWith('blob:'), 'el enlace es blob:, no http://localhost:5557');
  assert.strictEqual(l.links[0].download, 'Libro \u00e1 \u00e9.m4b');
  assert.strictEqual(l.links[0].clicks, 1);
  assert.deepStrictEqual(l.locationWrites, [], 'no se asigno location');
  assert.deepStrictEqual(l.revokes, [], 'revokeObjectURL diferido, no inmediato');
  assert.deepStrictEqual(l.timers, [30000]);
  assert.ok(l.toasts.some(m => m.indexOf('Descargando') === 0), 'toast de descarga: ' + l.toasts);
  assert.strictEqual(env.button.disabled, false, 'el boton se rehabilita');
  console.log('ok  descarga correcta: fetch + blob, sin navegar');
}

async function caseNotFound() {
  const env = makeEnv(async () => ({ ok: false, status: 404, json: async () => ({ error: 'Archivo no encontrado' }) }));
  env.api.showResult(Object.assign({}, RESULT));
  await env.api.downloadM4B();
  const l = env.log;
  assert.strictEqual(l.links.length, 0, 'sin enlace si el servidor responde 404');
  assert.ok(l.toasts.some(m => m.indexOf('Archivo no encontrado') >= 0 && m.indexOf('404') >= 0),
            'el motivo llega al usuario: ' + l.toasts);
  assert.deepStrictEqual(l.locationWrites, []);
  assert.strictEqual(env.button.disabled, false);
  console.log('ok  404: se informa el motivo, sin enlace');
}

async function caseNetworkError() {
  const env = makeEnv(async () => { throw new Error('Failed to fetch'); });
  env.api.showResult(Object.assign({}, RESULT));
  await env.api.downloadM4B();
  assert.strictEqual(env.log.links.length, 0);
  assert.ok(env.log.toasts.some(m => m.indexOf('Failed to fetch') >= 0), String(env.log.toasts));
  assert.strictEqual(env.button.disabled, false);
  console.log('ok  error de red: se informa el motivo');
}

async function caseNoResult() {
  const env = makeEnv(async () => { throw new Error('no debe llamarse'); });
  await env.api.downloadM4B();
  assert.strictEqual(env.log.fetches.length, 0);
  assert.ok(env.log.toasts.some(m => m.indexOf('No hay archivo') === 0));
  console.log('ok  sin resultado: aviso, sin peticion');
}

(async () => {
  await caseOk();
  await caseNotFound();
  await caseNetworkError();
  await caseNoResult();
  console.log('todos los casos pasaron');
})().catch(e => { console.error('FALLO:', e && e.stack || e); process.exit(1); });
