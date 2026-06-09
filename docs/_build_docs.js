/**
 * Build script for neven-docs.html
 * 
 * Reads the 11 docusaurus markdown chapters and generates a single
 * self-contained HTML documentation viewer with dark theme.
 * 
 * Usage: node _build_docs.js
 * Output: neven-docs.html (in same directory)
 */

console.log('BUILD SCRIPT STARTING...');
const fs = require('fs');
const path = require('path');

const CHAPTERS = [
  { file: 'docusaurus/00-portada.md',          title: 'Portada' },
  { file: 'docusaurus/01-introduccion.md',      title: 'Introduccion' },
  { file: 'docusaurus/02-instalacion.md',       title: 'Instalacion' },
  { file: 'docusaurus/03-arquitectura.md',      title: 'Arquitectura' },
  { file: 'docusaurus/04-funciones-julia.md',   title: 'Funciones Julia' },
  { file: 'docusaurus/05-funciones-r.md',       title: 'Funciones R' },
  { file: 'docusaurus/06-pluto-quarto.md',      title: 'Pluto y Quarto' },
  { file: 'docusaurus/07-webview2-ribbon.md',   title: 'WebView2 y Ribbon' },
  { file: 'docusaurus/08-seguridad-testing.md', title: 'Seguridad y Testing' },
  { file: 'docusaurus/09-mantenimiento.md',     title: 'Mantenimiento' },
  { file: 'docusaurus/10-ejemplos.md',          title: 'Ejemplos' },
  { file: 'docusaurus/11-diccionario-funciones.md', title: 'Diccionario de Funciones' },
];

const docsDir = __dirname;

function readChapter(filePath) {
  var full = fs.readFileSync(path.join(docsDir, filePath), 'utf8');
  var stripped = full.replace(/^---[\s\S]*?---\s*\n?/, '');
  return stripped.trim();
}

function b64(str) {
  return Buffer.from(str, 'utf8').toString('base64');
}

var chapterData = CHAPTERS.map(function(ch) {
  return b64(readChapter(ch.file));
});

var titles = CHAPTERS.map(function(ch) { return ch.title; });

var parts = [];

parts.push('<!DOCTYPE html>');
parts.push('<html lang="es">');
parts.push('<head>');
parts.push('<meta charset="UTF-8">');
parts.push('<title>NEVEN v2.0 - Documentacion</title>');
parts.push('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">');
parts.push('<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></scr' + 'ipt>');
parts.push('<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></scr' + 'ipt>');
parts.push('<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></scr' + 'ipt>');

parts.push('<style>');
parts.push('*{margin:0;padding:0;box-sizing:border-box}');
parts.push('body{font-family:"Segoe UI",sans-serif;background:#1e1e1e;color:#e0e0e0;display:flex;flex-direction:column;height:100vh;overflow:hidden}');
parts.push('.header{background:#252525;border-bottom:2px solid #a0e515;padding:14px 28px;display:flex;align-items:center;gap:18px;flex-shrink:0}');
parts.push('.header .brand{font-size:26px;font-weight:700;color:#a0e515;letter-spacing:3px}');
parts.push('.header .subtitle{font-size:14px;color:#888;border-left:1px solid #444;padding-left:18px}');
parts.push('.layout{display:flex;flex:1;overflow:hidden}');
parts.push('.sidebar{width:260px;min-width:260px;background:#252525;border-right:1px solid #333;overflow-y:auto;padding:16px 0}');
parts.push('.sidebar-title{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#666;padding:8px 20px 12px}');
parts.push('.sidebar-item{display:block;padding:10px 20px;color:#bbb;font-size:14px;cursor:pointer;transition:all .2s;border-left:3px solid transparent}');
parts.push('.sidebar-item:hover{background:#2a2a2a;color:#a0e515;border-left-color:#a0e51566}');
parts.push('.sidebar-item.active{background:#1e1e1e;color:#a0e515;border-left-color:#a0e515;font-weight:600}');
parts.push('.sidebar-item .n{display:inline-block;width:28px;color:#666;font-size:12px}');
parts.push('.sidebar-item.active .n{color:#a0e515}');
parts.push('.main{flex:1;overflow-y:auto;padding:36px 48px 60px}');
parts.push('#content h1{font-size:28px;color:#a0e515;margin-bottom:20px;padding-bottom:10px;border-bottom:1px solid #333}');
parts.push('#content h2{font-size:22px;color:#c8e86e;margin-top:36px;margin-bottom:14px}');
parts.push('#content h3{font-size:17px;color:#d0d0d0;margin-top:24px;margin-bottom:10px}');
parts.push('#content p{line-height:1.7;margin-bottom:12px;color:#ccc}');
parts.push('#content a{color:#a0e515}');
parts.push('#content strong{color:#e0e0e0}');
parts.push('#content ul,#content ol{margin:10px 0 14px 24px;line-height:1.7}');
parts.push('#content li{margin-bottom:4px;color:#ccc}');
parts.push('#content hr{border:none;border-top:1px solid #333;margin:28px 0}');
parts.push('#content table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px}');
parts.push('#content thead th{background:#2a2a2a;color:#a0e515;padding:10px 14px;text-align:left;border:1px solid #3a3a3a}');
parts.push('#content tbody td{padding:8px 14px;border:1px solid #333;color:#ccc}');
parts.push('#content tbody tr:nth-child(even){background:#242424}');
parts.push('#content tbody tr:hover{background:#2c2c2c}');
parts.push('#content pre{background:#161616;border:1px solid #333;border-radius:6px;padding:16px;overflow-x:auto;margin:12px 0 16px}');
parts.push('#content pre code{color:#d4d4d4;font-family:Consolas,monospace;background:none;padding:0;border:none;font-size:13px}');
parts.push('#content code{background:#2a2a2a;color:#ce9178;padding:2px 6px;border-radius:3px;font-family:Consolas,monospace;font-size:13px}');
parts.push('#content blockquote{border-left:3px solid #a0e515;padding:8px 16px;margin:12px 0;background:#242424;color:#bbb}');
parts.push('.katex{color:#e0e0e0}');
parts.push('</style>');
parts.push('</head>');
parts.push('<body>');
parts.push('<div class="header">');
parts.push('  <div class="brand">NEVEN</div>');
parts.push('  <div class="subtitle">Documentacion v2.0 &mdash; Sistema Multilenguaje para Excel</div>');
parts.push('</div>');
parts.push('<div class="layout">');
parts.push('  <nav class="sidebar" id="sidebar">');
parts.push('    <div class="sidebar-title">Capitulos</div>');
parts.push('  </nav>');
parts.push('  <main class="main"><div id="content"></div></main>');
parts.push('</div>');

// Build the script section
var script = [];
script.push('<scr' + 'ipt>');
script.push('var chData = ' + JSON.stringify(chapterData) + ';');
script.push('var titles = ' + JSON.stringify(titles) + ';');
script.push('');
script.push('function b64decode(str) {');
script.push('  var bin = atob(str);');
script.push('  var bytes = new Uint8Array(bin.length);');
script.push('  for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);');
script.push('  return new TextDecoder("utf-8").decode(bytes);');
script.push('}');
script.push('');
script.push('var sidebar = document.getElementById("sidebar");');
script.push('var contentEl = document.getElementById("content");');
script.push('var activeIdx = 0;');
script.push('');
script.push('titles.forEach(function(t, i) {');
script.push('  var item = document.createElement("div");');
script.push('  item.className = "sidebar-item" + (i === 0 ? " active" : "");');
script.push('  item.innerHTML = \'<span class="n">\' + i + \'.</span> \' + t;');
script.push('  item.addEventListener("click", function() { loadCh(i); });');
script.push('  sidebar.appendChild(item);');
script.push('});');
script.push('');
script.push('function loadCh(idx) {');
script.push('  var items = sidebar.querySelectorAll(".sidebar-item");');
script.push('  items[activeIdx].classList.remove("active");');
script.push('  items[idx].classList.add("active");');
script.push('  activeIdx = idx;');
script.push('  var md = b64decode(chData[idx]);');
script.push('  md = md.replace(/^:::(?:note|tip|warning|info)\\s*$/gm, "> **Nota:**");');
script.push('  md = md.replace(/^:::$/gm, "");');
script.push('  contentEl.innerHTML = marked.parse(md);');
script.push('  document.querySelector(".main").scrollTop = 0;');
script.push('  if (typeof renderMathInElement === "function") {');
script.push('    renderMathInElement(contentEl, {');
script.push('      delimiters: [');
script.push('        {left: "$$", right: "$$", display: true},');
script.push('        {left: "$", right: "$", display: false}');
script.push('      ],');
script.push('      throwOnError: false');
script.push('    });');
script.push('  }');
script.push('  document.querySelector(".main").scrollTop = 0;');
script.push('}');
script.push('');
script.push('loadCh(0);');
script.push('// Global handler: intercept ALL anchor link clicks to prevent page navigation');
script.push('document.addEventListener("click", function(e) {');
script.push('  var a = e.target.closest("a");');
script.push('  if (!a) return;');
script.push('  var href = a.getAttribute("href");');
script.push('  if (!href || !href.startsWith("#")) return;');
script.push('  e.preventDefault();');
script.push('  e.stopPropagation();');
script.push('  var tid = decodeURIComponent(href.substring(1));');
script.push('  var el = document.getElementById(tid);');
script.push('  if (!el) {');
script.push('    var norm = tid.toLowerCase().replace(/[^\\w\\u00C0-\\u024F]+/g, "-").replace(/^-|-$/g, "");');
script.push('    el = document.getElementById(norm);');
script.push('  }');
script.push('  if (!el) {');
script.push('    // Last resort: search all headers for matching text');
script.push('    var headers = contentEl.querySelectorAll("h1,h2,h3,h4,h5,h6");');
script.push('    var searchText = tid.replace(/-/g, " ").toLowerCase();');
script.push('    for (var i = 0; i < headers.length; i++) {');
script.push('      var hText = headers[i].textContent.toLowerCase().trim();');
script.push('      if (hText === searchText || hText.indexOf(searchText) !== -1 || headers[i].id === tid) {');
script.push('        el = headers[i]; break;');
script.push('      }');
script.push('    }');
script.push('  }');
script.push('  if (el) { el.scrollIntoView({ behavior: "smooth", block: "start" }); }');
script.push('}, true);');
script.push('</scr' + 'ipt>');
script.push('</body>');
script.push('</html>');

parts = parts.concat(script);

var outPath = path.join(docsDir, 'neven-docs.html');
fs.writeFileSync(outPath, parts.join('\n'), 'utf8');

var stats = fs.statSync(outPath);
console.log('Generated: ' + outPath);
console.log('Chapters: ' + CHAPTERS.length);
console.log('Size: ' + (stats.size / 1024).toFixed(1) + ' KB');
