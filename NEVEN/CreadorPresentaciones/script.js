/* =================================================================
   NEVEN CreadorPresentaciones — script.js
   Fixes aplicados:
   - XSS: texto de slides sanitizado antes de inyectar en HTML
   - Memory leak: drag listeners registrados una sola vez con AbortController
   - Debounce en saveState para inputs de texto
   - Preview con srcdoc (no depende de preview.html externo)
   - Nombre de archivo configurable en export
   - Undo/Redo con Ctrl+Z / Ctrl+Y
   - via.placeholder.com → placehold.co
   - COLOR_PALETTES como propiedad estática
   - Título de presentación editable
   ================================================================= */

'use strict';

// ── Utilidades de seguridad ────────────────────────────────────────
function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sanitizeForAttr(str) {
  return escapeHtml(str);
}

// Permite **negrita** e *italic* pero escapa todo lo demás
function formatSlideText(text) {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}

// Debounce genérico
function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ── Paletas de colores (static-like, fuera de la clase) ───────────
const COLOR_PALETTES = {
  default:     { bg: ['rgba(168,230,0,.8)','rgba(54,162,235,.8)','rgba(255,206,86,.8)','rgba(75,192,192,.8)','rgba(153,102,255,.8)','rgba(255,159,64,.8)'],   border: ['rgba(168,230,0,1)','rgba(54,162,235,1)','rgba(255,206,86,1)','rgba(75,192,192,1)','rgba(153,102,255,1)','rgba(255,159,64,1)'] },
  blue:        { bg: ['rgba(54,162,235,.8)','rgba(75,192,192,.8)','rgba(100,149,237,.8)','rgba(30,144,255,.8)','rgba(70,130,180,.8)','rgba(153,102,255,.8)'],  border: ['rgba(54,162,235,1)','rgba(75,192,192,1)','rgba(100,149,237,1)','rgba(30,144,255,1)','rgba(70,130,180,1)','rgba(153,102,255,1)'] },
  green:       { bg: ['rgba(168,230,0,.8)','rgba(144,238,144,.8)','rgba(60,179,113,.8)','rgba(46,125,50,.8)','rgba(102,187,106,.8)','rgba(129,199,132,.8)'],   border: ['rgba(168,230,0,1)','rgba(144,238,144,1)','rgba(60,179,113,1)','rgba(46,125,50,1)','rgba(102,187,106,1)','rgba(129,199,132,1)'] },
  warm:        { bg: ['rgba(255,99,132,.8)','rgba(255,159,64,.8)','rgba(255,206,86,.8)','rgba(255,140,0,.8)','rgba(220,20,60,.8)','rgba(255,69,0,.8)'],        border: ['rgba(255,99,132,1)','rgba(255,159,64,1)','rgba(255,206,86,1)','rgba(255,140,0,1)','rgba(220,20,60,1)','rgba(255,69,0,1)'] },
  cool:        { bg: ['rgba(54,162,235,.8)','rgba(153,102,255,.8)','rgba(75,192,192,.8)','rgba(147,112,219,.8)','rgba(106,90,205,.8)','rgba(72,61,139,.8)'],   border: ['rgba(54,162,235,1)','rgba(153,102,255,1)','rgba(75,192,192,1)','rgba(147,112,219,1)','rgba(106,90,205,1)','rgba(72,61,139,1)'] },
  monochrome:  { bg: ['rgba(128,128,128,.8)','rgba(169,169,169,.8)','rgba(105,105,105,.8)','rgba(192,192,192,.8)','rgba(64,64,64,.8)','rgba(211,211,211,.8)'], border: ['rgba(128,128,128,1)','rgba(169,169,169,1)','rgba(105,105,105,1)','rgba(192,192,192,1)','rgba(64,64,64,1)','rgba(211,211,211,1)'] }
};

// ── Clase principal ────────────────────────────────────────────────
class PresentationEditor {
  constructor() {
    this.slides        = [];
    this.currentSlide  = null;
    this.slideCounter  = 0;
    this.history       = [];
    this.historyIndex  = -1;
    this.title         = 'Mi Presentación';

    // AbortController para drag listeners — evita memory leaks
    this._dragAbort    = null;

    // Workbook activo para gráficos
    this._workbook     = null;
    this._sheetData    = {};

    this._init();
  }

  _init() {
    this._cacheElements();
    this._bindToolbar();
    this._bindProperties();
    this._bindModals();
    this._bindKeyboard();
    // Iniciar con canvas vacío — el usuario puede cargar los ejemplos con "Ver Ejemplos"
    this._updateStatus();
    this._renderList();
  }

  // ── Cache de elementos DOM ───────────────────────────────────────
  _cacheElements() {
    this.el = {
      slidesList:   document.getElementById('slides-list'),
      canvas:       document.getElementById('canvas'),
      statusSlides: document.getElementById('status-slides'),
      statusSel:    document.getElementById('status-selected'),
      // Propiedades
      text:         document.getElementById('prop-text'),
      type:         document.getElementById('prop-type'),
      x:            document.getElementById('prop-x'),
      y:            document.getElementById('prop-y'),
      z:            document.getElementById('prop-z'),
      rotate:       document.getElementById('prop-rotate'),
      scale:        document.getElementById('prop-scale'),
      fontFamily:   document.getElementById('prop-font-family'),
      fontSize:     document.getElementById('prop-font-size'),
      textColor:    document.getElementById('prop-text-color'),
      imageUrl:     document.getElementById('prop-image-url'),
      iframeUrl:    document.getElementById('prop-iframe-url'),
      palette:      document.getElementById('prop-palette'),
      chartFile:    document.getElementById('prop-chart-file'),
      grpImage:     document.getElementById('grp-image'),
      grpIframe:    document.getElementById('grp-iframe'),
      grpChart:     document.getElementById('grp-chart'),
      contentWidth:  null,
      contentHeight: null,
      contentZoom:      document.getElementById('prop-content-zoom'),
      contentOffsetX:   document.getElementById('prop-content-offset-x'),
      contentOffsetY:   document.getElementById('prop-content-offset-y'),
      slideSelector:    document.getElementById('prop-slide-selector'),
      // Preview modal
      modalPreview:        document.getElementById('modal-preview'),
      previewFrame:        document.getElementById('preview-frame'),
      btnClosePreview:     document.getElementById('btn-close-preview'),
      // Blackboard modal
      modalBlackboard:     document.getElementById('modal-blackboard'),
      bbCanvas:            document.getElementById('blackboard-canvas'),
      chalkSize:           document.getElementById('chalk-size'),
      btnClearBoard:       document.getElementById('btn-clear-board'),
      btnSaveBlackboard:   document.getElementById('btn-save-blackboard'),
      btnCancelBlackboard: document.getElementById('btn-cancel-blackboard'),
      btnCloseBlackboard:  document.getElementById('btn-close-blackboard'),
      // Chart modal
      modalChart:          document.getElementById('modal-chart'),
      chartSheet:          document.getElementById('chart-sheet'),
      chartType:           document.getElementById('chart-type'),
      chartXType:          document.getElementById('chart-x-type'),
      chartXVar:           document.getElementById('chart-x-var'),
      chartColumns:        document.getElementById('chart-columns'),
      chartRecords:        document.getElementById('chart-records'),
      grpXType:            document.getElementById('grp-x-type'),
      grpXVar:             document.getElementById('grp-x-var'),
      btnGenerateChart:    document.getElementById('btn-generate-chart'),
      btnCancelChart:      document.getElementById('btn-cancel-chart'),
      btnCloseChart:       document.getElementById('btn-close-chart'),
    };
  }

  // ── Toolbar ──────────────────────────────────────────────────────
  _bindToolbar() {
    document.getElementById('btn-add-slide').addEventListener('click', () => this.addSlide());
    document.getElementById('btn-delete-slide').addEventListener('click', () => this.deleteSlide());
    document.getElementById('btn-preview').addEventListener('click', () => this.showPreview());
    document.getElementById('btn-export').addEventListener('click', () => this.exportPresentation());
    document.getElementById('btn-load').addEventListener('click', () => document.getElementById('html-file-input').click());
    document.getElementById('btn-load-demo').addEventListener('click', () => this._loadDefaultSlides());
    document.getElementById('btn-clear-slides').addEventListener('click', () => {
      if (this.slides.length === 0) return;
      if (!confirm('¿Eliminar todos los slides?')) return;
      this.slides = [];
      this.currentSlide = null;
      this.slideCounter = 0;
      this._renderList();
      this._renderCanvas();
      this._updateStatus();
      this._saveState();
    });
    document.getElementById('html-file-input').addEventListener('change', e => this.loadPresentation(e));
    document.getElementById('btn-undo').addEventListener('click', () => this.undo());
    document.getElementById('btn-redo').addEventListener('click', () => this.redo());

    // Selector de slide en panel de propiedades
    if (this.el.slideSelector) {
      this.el.slideSelector.addEventListener('change', () => {
        const idx = parseInt(this.el.slideSelector.value);
        if (!isNaN(idx) && this.slides[idx]) {
          this._selectSlide(this.slides[idx]);
        }
      });
    }
  }

  // ── Propiedades — debounce en texto para no saturar el historial ──
  _bindProperties() {
    const debouncedSave = debounce(() => this._commitSlideUpdate(), 400);

    // Cada campo actualiza SOLO su propiedad en currentSlide — nunca el slide entero
    const propMap = [
      // [elemento,  fn-escritura,                             debounce?]
      [this.el.type,          s => {
        s.type = this.el.type.value;
        this._toggleTypeControls();
        if (s.type === 'blackboard') this._openBlackboard();
      }],
      [this.el.x,             s => { s.x          = parseInt(this.el.x.value)           || 0; }],
      [this.el.y,             s => { s.y          = parseInt(this.el.y.value)           || 0; }],
      [this.el.z,             s => { s.z          = parseInt(this.el.z.value)           || 0; }],
      [this.el.rotate,        s => { s.rotate     = parseInt(this.el.rotate.value)      || 0; }],
      [this.el.scale,         s => { s.scale      = parseFloat(this.el.scale.value)     || 1; }],
      [this.el.fontFamily,    s => { s.fontFamily = this.el.fontFamily.value; }],
      [this.el.fontSize,      s => { s.fontSize   = parseInt(this.el.fontSize.value)    || 48; }],
      [this.el.textColor,     s => { s.textColor  = this.el.textColor.value; }],
      [this.el.imageUrl,      s => { s.imageUrl   = this.el.imageUrl.value.trim(); }],
      [this.el.iframeUrl,     s => { s.iframeUrl  = this.el.iframeUrl.value.trim(); }],
      [this.el.contentZoom,   s => { s.contentZoom    = parseFloat(this.el.contentZoom.value)    || 1.0; }],
      [this.el.contentOffsetX,s => { s.contentOffsetX = parseFloat(this.el.contentOffsetX.value) ?? 50; }],
      [this.el.contentOffsetY,s => { s.contentOffsetY = parseFloat(this.el.contentOffsetY.value) ?? 50; }],
    ];

    // Textarea de texto — debounced para no saturar historial
    this.el.text.addEventListener('input', () => {
      if (!this.currentSlide) return;
      this.currentSlide.text = this.el.text.value;
      this._renderCanvas();
      this._updateCurrentSlideLabel();    // actualiza label sin reconstruir lista
      debouncedSave();
    });

    propMap.forEach(([el, writeFn]) => {
      if (!el) return;
      const handler = () => {
        if (!this.currentSlide) return;
        writeFn(this.currentSlide);          // escribe SOLO esta propiedad al slide activo
        this._renderCanvas();
        this._updateCurrentSlideLabel();     // actualiza solo el label, no reconstruye la lista
        this._saveState();
      };
      el.addEventListener('input',  handler);
      el.addEventListener('change', handler);
    });

    this.el.chartFile.addEventListener('change', e => this._handleChartFile(e));
  }

  // _updateFromPanel queda como NO-OP para no romper llamadas residuales
  // La lógica fue migrada a propMap en _bindProperties
  _updateFromPanel() {
    // Deprecated — cada campo actualiza directamente su propiedad en _bindProperties
    // Se mantiene solo para no romper llamadas externas (ej: _attachPropsToPreview sync)
    if (!this.currentSlide) return;
  }

  // ── Modales ───────────────────────────────────────────────────────
  _bindModals() {
    // Preview
    this.el.btnClosePreview.addEventListener('click', () => {
      this._closeModal(this.el.modalPreview);
      // Ocultar overlay de propiedades al cerrar preview
      const ov = document.getElementById('preview-props-overlay');
      if (ov) ov.style.display = 'none';
    });

    // Blackboard
    this.el.btnCloseBlackboard.addEventListener('click', () => this._closeModal(this.el.modalBlackboard));
    this.el.btnCancelBlackboard.addEventListener('click', () => this._closeModal(this.el.modalBlackboard));
    this.el.btnSaveBlackboard.addEventListener('click', () => this._saveBlackboard());
    this.el.btnClearBoard.addEventListener('click', () => this._clearBoard());

    // Chalk color buttons
    document.querySelectorAll('.btn-chalk[data-color]').forEach(btn => {
      btn.addEventListener('click', e => {
        document.querySelectorAll('.btn-chalk').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
      });
    });

    // Chart modal
    this.el.btnCloseChart.addEventListener('click', () => this._closeModal(this.el.modalChart));
    this.el.btnCancelChart.addEventListener('click', () => this._closeModal(this.el.modalChart));
    this.el.btnGenerateChart.addEventListener('click', () => this._generateChart());
    this.el.chartType.addEventListener('change', () => this._updateChartModalControls());
    this.el.chartSheet.addEventListener('change', e => this._populateColumns(e.target.value));

    // Close modals on backdrop click
    [this.el.modalPreview, this.el.modalBlackboard, this.el.modalChart].forEach(m => {
      m.addEventListener('click', e => {
        if (e.target === m) {
          this._closeModal(m);
          if (m === this.el.modalPreview) {
            const ov = document.getElementById('preview-props-overlay');
            if (ov) ov.style.display = 'none';
          }
        }
      });
    });
  }

  // ── Keyboard shortcuts ────────────────────────────────────────────
  _bindKeyboard() {
    document.addEventListener('keydown', e => {
      if (e.ctrlKey && e.key === 'z') { e.preventDefault(); this.undo(); }
      if (e.ctrlKey && e.key === 'y') { e.preventDefault(); this.redo(); }
    });
  }

  _openModal(el)  { el.classList.add('show'); }
  _closeModal(el) { el.classList.remove('show'); }

  // ── Slides por defecto ────────────────────────────────────────────
  _loadDefaultSlides() {
    this.slides = [
      this._newSlide({ id:'s-1', text:'Esta presentación', x:-3410, y:-1745, scale:1 }),
      this._newSlide({ id:'s-2', text:'fue creada con la intención de\npermitir a todos crear', x:-405, y:-2960 }),
      this._newSlide({ id:'s-3', text:'presentaciones\nprofesionales', x:905, y:-1590 }),
      this._newSlide({ id:'s-4', text:'sin escribir\nlíneas de código', x:-1035, y:-440, scale:4 }),
      this._newSlide({ id:'s-5', text:'con objetos interactivos', x:830, y:2995, rotate:90, scale:5 }),
      this._newSlide({ id:'s-6', text:'y colores NEVEN', x:4295, y:-2770, z:-3000, rotate:300, textColor:'#a8e600' }),
      this._newSlide({ id:'s-7', text:'GRANDES', x:6700, y:-300, scale:6, fontSize:120, textColor:'#a8e600' }),
      this._newSlide({ id:'s-8', text:'medianos', x:6300, y:2000, rotate:20, scale:4, fontSize:60 }),
      this._newSlide({ id:'s-9', text:'pequeños', x:3485, y:2920, scale:2, fontSize:30 }),
      this._newSlide({ id:'s-10', text:'Incluye gráficos interactivos\ncon datos desde Excel', x:-635, y:1240, z:-100, rotate:-40, scale:2 }),
      this._newSlide({ id:'s-chart', text:'', x:2380, y:-2995, type:'chart', charts:[{id:'demo', config:{type:'bar',data:{labels:['Ene','Feb','Mar','Abr','May'],datasets:[{label:'Demo',data:[23.5,45.2,67.8,34.1,56.7],backgroundColor:'rgba(168,230,0,0.8)',borderColor:'rgba(168,230,0,1)',borderWidth:1}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#e0e0e0'}}},scales:{y:{ticks:{color:'#888'},grid:{color:'rgba(255,255,255,0.08)'}},x:{ticks:{color:'#888'},grid:{color:'rgba(255,255,255,0.08)'}}}}}}] }),
      this._newSlide({ id:'s-11', text:'Pizarras interactivas\npara ilustrar en vivo', x:-4320, y:-2975 }),
      this._newSlide({ id:'s-bb', text:'', x:-3580, y:-385, scale:2, type:'blackboard' }),
      this._newSlide({ id:'s-12', text:'Embebe sitios web', x:-2445, y:840 }),
      this._newSlide({ id:'s-iframe', text:'', x:-4545, y:1530, type:'iframe', iframeUrl:'https://es.wikipedia.org/wiki/Wikipedia:Portada' }),
      this._newSlide({ id:'s-13', text:'Agrega imágenes', x:-3380, y:2625, scale:10 }),
      this._newSlide({ id:'s-img', text:'', x:705, y:-120, type:'image', imageUrl:'https://placehold.co/800x600/1a1a1a/a8e600?text=Imagen+de+Ejemplo' }),
      this._newSlide({ id:'s-fin', text:'Con todo gusto!\nNEVEN Studio', x:1705, y:0, textColor:'#a8e600' }),
    ];
    this.slideCounter = this.slides.length;
    this._renderList();
    this._selectSlide(this.slides[0]);
    this._saveState();
  }

  _newSlide(overrides = {}) {
    return Object.assign({
      id:            `slide-${++this.slideCounter}`,
      text:          'Nuevo Slide',
      type:          'slide',
      x: 0, y: 0, z: 0,
      rotate: 0,  scale: 1,
      fontFamily:    "'Segoe UI', sans-serif",
      fontSize:      48,
      textColor:     '#e0e0e0',
      imageUrl:      '',
      iframeUrl:     '',
      charts:        [],
      blackboardData:  null,
      contentZoom:     1.0,  // zoom del contenido embebido (transform:scale)
      contentOffsetX:  50,   // posición horizontal del contenido dentro del slide (%)
      contentOffsetY:  50,   // posición vertical del contenido dentro del slide (%)
    }, overrides);
  }

  // ── CRUD de slides ─────────────────────────────────────────────────
  addSlide() {
    const lastX = this.slides.length ? this.slides[this.slides.length - 1].x + 1200 : 0;
    const s = this._newSlide({ text: 'Nuevo Slide', x: lastX });
    this.slides.push(s);
    this._renderList();
    this._selectSlide(s);
    this._saveState();
  }

  deleteSlide() {
    if (!this.currentSlide || this.slides.length <= 1) return;
    const idx = this.slides.indexOf(this.currentSlide);
    this.slides.splice(idx, 1);
    this._selectSlide(this.slides[Math.min(idx, this.slides.length - 1)]);
    this._renderList();
    this._renderCanvas();
    this._saveState();
  }

  // ── Selección y panel ─────────────────────────────────────────────
  _selectSlide(slide) {
    this.currentSlide = slide;
    this._fillPanel();
    this._renderCanvas();
    this._highlightListItem();
    this._updateStatus();
    this._syncSlideSelectorValue();  // mantener selector en sync sin reconstruirlo
  }

  // Actualiza solo el valor del selector sin reconstruirlo
  _syncSlideSelectorValue() {
    if (!this.el.slideSelector || !this.currentSlide) return;
    const idx = this.slides.indexOf(this.currentSlide);
    if (idx >= 0) this.el.slideSelector.value = idx;
  }

  // Reconstruye el <select> del panel — llamar solo cuando cambia la lista de slides
  _rebuildSlideSelector() {
    const sel = this.el.slideSelector;
    if (!sel) return;
    const currentIdx = this.currentSlide ? this.slides.indexOf(this.currentSlide) : -1;
    sel.innerHTML = '';
    this.slides.forEach((s, i) => {
      const opt = document.createElement('option');
      opt.value = i;
      const label = s.text ? s.text.substring(0, 28).replace(/\n/g, ' ') : s.type;
      opt.textContent = `${i + 1}. ${label || s.type}`;
      sel.appendChild(opt);
    });
    if (currentIdx >= 0) sel.value = currentIdx;
  }

  // Actualiza solo el label del slide activo en la lista lateral — sin reconstruir el DOM completo
  _updateCurrentSlideLabel() {
    if (!this.currentSlide) return;
    const idx = this.slides.indexOf(this.currentSlide);
    if (idx < 0) return;
    const card = this.el.slidesList.querySelector(`.slide-card[data-idx="${idx}"]`);
    if (card) {
      const labelEl = card.querySelector('.slide-label');
      if (labelEl) {
        const s = this.currentSlide;
        labelEl.textContent = escapeHtml(s.text.substring(0, 22)) || s.type;
      }
    }
    // Actualizar también el option del selector
    if (this.el.slideSelector) {
      const opt = this.el.slideSelector.options[idx];
      if (opt) {
        const s = this.currentSlide;
        const label = s.text ? s.text.substring(0, 28).replace(/\n/g, ' ') : s.type;
        opt.textContent = `${idx + 1}. ${label || s.type}`;
      }
    }
  }

  _fillPanel() {
    const s = this.currentSlide;
    if (!s) return;
    this.el.text.value       = s.text;
    this.el.type.value       = s.type;
    this.el.x.value          = s.x;
    this.el.y.value          = s.y;
    this.el.z.value          = s.z;
    this.el.rotate.value     = s.rotate;
    this.el.scale.value      = s.scale;
    this.el.fontFamily.value = s.fontFamily || "'Segoe UI', sans-serif";
    this.el.fontSize.value   = s.fontSize   || 48;
    // Color: convert rgb() to hex for the color input
    this.el.textColor.value  = this._toHex(s.textColor) || '#e0e0e0';
    this.el.imageUrl.value   = s.imageUrl  || '';
    this.el.iframeUrl.value  = s.iframeUrl || '';
    this._toggleTypeControls();
    // Zoom y offset del contenido embebido
    if (this.el.contentZoom)    this.el.contentZoom.value    = s.contentZoom    != null ? s.contentZoom    : 1.0;
    if (this.el.contentOffsetX) this.el.contentOffsetX.value = s.contentOffsetX != null ? s.contentOffsetX : 50;
    if (this.el.contentOffsetY) this.el.contentOffsetY.value = s.contentOffsetY != null ? s.contentOffsetY : 50;
  }

  _toHex(color) {
    if (!color) return '#e0e0e0';
    if (color.startsWith('#')) return color;
    const d = document.createElement('div');
    d.style.color = color;
    document.body.appendChild(d);
    const c = getComputedStyle(d).color;
    document.body.removeChild(d);
    const m = c.match(/\d+/g);
    if (!m || m.length < 3) return '#e0e0e0';
    return '#' + m.slice(0,3).map(n => parseInt(n).toString(16).padStart(2,'0')).join('');
  }

  _updateFromPanel() {
    if (!this.currentSlide) return;
    const s = this.currentSlide;
    s.type       = this.el.type.value;
    s.x          = parseInt(this.el.x.value)      || 0;
    s.y          = parseInt(this.el.y.value)       || 0;
    s.z          = parseInt(this.el.z.value)       || 0;
    s.rotate     = parseInt(this.el.rotate.value)  || 0;
    s.scale      = parseFloat(this.el.scale.value) || 1;
    s.fontFamily = this.el.fontFamily.value;
    s.fontSize   = parseInt(this.el.fontSize.value)|| 48;
    s.textColor  = this.el.textColor.value;
    s.imageUrl      = this.el.imageUrl.value.trim();
    s.iframeUrl     = this.el.iframeUrl.value.trim();
    s.contentZoom    = parseFloat(this.el.contentZoom    && this.el.contentZoom.value)    || 1.0;
    s.contentOffsetX = parseFloat(this.el.contentOffsetX && this.el.contentOffsetX.value) ?? 50;
    s.contentOffsetY = parseFloat(this.el.contentOffsetY && this.el.contentOffsetY.value) ?? 50;

    if (s.type === 'blackboard') this._openBlackboard();

    this._toggleTypeControls();
    this._renderCanvas();
    this._renderList();
    this._saveState();
  }

  _commitSlideUpdate() {
    this._saveState();
  }

  _toggleTypeControls() {
    const t = this.el.type.value;
    this.el.grpImage.style.display  = t === 'image'      ? 'block' : 'none';
    this.el.grpIframe.style.display = t === 'iframe'     ? 'block' : 'none';
    this.el.grpChart.style.display  = t === 'chart'      ? 'block' : 'none';
  }

  _updateStatus() {
    this.el.statusSlides.textContent = `${this.slides.length} slides`;
    this.el.statusSel.textContent = this.currentSlide
      ? `#${this.slides.indexOf(this.currentSlide)+1} — ${this.currentSlide.type}`
      : '—';
    // T5: coordenadas del slide activo
    var coordsEl = document.getElementById('status-coords');
    if (coordsEl && this.currentSlide) {
      coordsEl.textContent = `X:${this.currentSlide.x} Y:${this.currentSlide.y}`;
    } else if (coordsEl) {
      coordsEl.textContent = '';
    }
  }

  // ── Render lista de slides ─────────────────────────────────────────
  _renderList() {
    const TYPE_ICONS = {
      slide:      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h16"/><path d="M4 10h12"/><path d="M4 14h14"/><path d="M4 18h8"/></svg>',
      title:      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 7h16"/><path d="M4 12h10"/></svg>',
      image:      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>',
      iframe:     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 8h18"/></svg>',
      chart:      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3v18h18"/><rect x="7" y="12" width="2" height="6"/><rect x="11" y="8" width="2" height="10"/><rect x="15" y="10" width="2" height="8"/></svg>',
      blackboard: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="4" width="18" height="12" rx="1"/><path d="M7 20h10M12 16v4"/></svg>',
      overview:   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>',
    };
    this.el.slidesList.innerHTML = '';
    this.slides.forEach((slide, idx) => {
      const div = document.createElement('div');
      div.className = 'slide-card' + (slide === this.currentSlide ? ' active' : '');
      div.draggable = true;
      div.dataset.idx = idx;
      div.innerHTML = `
        <span class="slide-icon">${TYPE_ICONS[slide.type] || TYPE_ICONS.slide}</span>
        <span class="slide-label">${escapeHtml(slide.text.substring(0,22)) || slide.type}</span>
        <span class="slide-num">${idx+1}</span>`;
      div.addEventListener('click', () => this._selectSlide(slide));
      // Drag-to-reorder
      div.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', idx));
      div.addEventListener('dragover',  e => e.preventDefault());
      div.addEventListener('drop', e => {
        e.preventDefault();
        const from = parseInt(e.dataTransfer.getData('text/plain'));
        const to   = parseInt(e.currentTarget.dataset.idx);
        if (from !== to) {
          const [moved] = this.slides.splice(from, 1);
          this.slides.splice(to, 0, moved);
          this._renderList();
          this._saveState();
        }
      });
      this.el.slidesList.appendChild(div);
    });
    this._updateStatus();
    this._rebuildSlideSelector();  // reconstruir selector cuando cambia la lista
  }

  _highlightListItem() {
    this.el.slidesList.querySelectorAll('.slide-card').forEach((c, i) => {
      c.classList.toggle('active', this.slides[i] === this.currentSlide);
    });
  }

  // ── Render canvas ─────────────────────────────────────────────────
  _renderCanvas() {
    // Cancelar drag listeners anteriores para evitar memory leak
    if (this._dragAbort) this._dragAbort.abort();
    this._dragAbort = new AbortController();
    const sig = { signal: this._dragAbort.signal };

    const cw = this.el.canvas.clientWidth  || 600;
    const ch = this.el.canvas.clientHeight || 400;
    const cx = cw / 2, cy = ch / 2;
    const zoom = this._zoom || 1.0;
    const divisor = 10 * zoom;

    // Tamaño base de cada slide en canvas — escala con zoom
    const SW = Math.round(110 * zoom);
    const SH = Math.round(72  * zoom);

    // T6: actualizar background-size del canvas con zoom
    this.el.canvas.style.backgroundSize = `${40 * zoom}px ${40 * zoom}px`;

    this.el.canvas.innerHTML = '';

    // ── Líneas de flujo SVG (antes de los slides para quedar detrás) ──
    if (this.slides.length > 1) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible';
      svg.setAttribute('width', cw);
      svg.setAttribute('height', ch);

      for (let i = 0; i < this.slides.length - 1; i++) {
        const a = this.slides[i];
        const b = this.slides[i + 1];

        const ax = Math.max(0, Math.min(cx + a.x / divisor - SW/2, cw - SW)) + SW/2;
        const ay = Math.max(0, Math.min(cy + a.y / divisor - SH/2, ch - SH)) + SH/2;
        const bx = Math.max(0, Math.min(cx + b.x / divisor - SW/2, cw - SW)) + SW/2;
        const by = Math.max(0, Math.min(cy + b.y / divisor - SH/2, ch - SH)) + SH/2;

        // Curva bezier suave entre centros
        const cp1x = ax + (bx - ax) * 0.5;
        const cp1y = ay;
        const cp2x = ax + (bx - ax) * 0.5;
        const cp2y = by;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M ${ax} ${ay} C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${bx} ${by}`);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', 'rgba(215,165,56,0.22)');
        path.setAttribute('stroke-width', '1.5');
        path.setAttribute('stroke-dasharray', '5,4');

        // Flecha pequeña en el destino
        const dx = bx - cp2x, dy = by - cp2y;
        const angle = Math.atan2(dy, dx);
        const aLen = 7;
        const ax1 = bx - aLen * Math.cos(angle - 0.4);
        const ay1 = by - aLen * Math.sin(angle - 0.4);
        const ax2 = bx - aLen * Math.cos(angle + 0.4);
        const ay2 = by - aLen * Math.sin(angle + 0.4);

        const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        arrow.setAttribute('d', `M ${ax1} ${ay1} L ${bx} ${by} L ${ax2} ${ay2}`);
        arrow.setAttribute('fill', 'none');
        arrow.setAttribute('stroke', 'rgba(215,165,56,0.35)');
        arrow.setAttribute('stroke-width', '1.5');
        arrow.setAttribute('stroke-linecap', 'round');

        // Número de orden en el punto medio
        const mx = (ax + bx) / 2, my = (ay + by) / 2;
        const txt = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        txt.setAttribute('x', mx); txt.setAttribute('y', my - 4);
        txt.setAttribute('text-anchor', 'middle');
        txt.setAttribute('font-size', '8');
        txt.setAttribute('fill', 'rgba(215,165,56,0.45)');
        txt.setAttribute('font-family', 'Segoe UI, sans-serif');
        txt.textContent = `${i + 1}→${i + 2}`;

        svg.appendChild(path);
        svg.appendChild(arrow);
        svg.appendChild(txt);
      }
      this.el.canvas.appendChild(svg);
    }

    this.slides.forEach(slide => {
      const el = document.createElement('div');
      el.className = 'slide-element' + (slide === this.currentSlide ? ' selected' : '');
      el.dataset.id = slide.id;

      // Aplicar tamaño escalado por zoom
      el.style.width  = SW + 'px';
      el.style.height = SH + 'px';
      el.style.fontSize = Math.max(7, Math.round(9 * zoom)) + 'px';

      // Rotación visual en el canvas
      if (slide.rotate) {
        el.style.transform = `rotate(${slide.rotate}deg)`;
        el.style.transformOrigin = 'center center';
      }

      const TYPE_LABELS = {
        image:'IMG', iframe:'WEB', chart:'CHART', blackboard:'PIZARRA', overview:'OVERVIEW', plotly:'PLOTLY'
      };
      el.textContent = (slide.type === 'plotly')
        ? (slide.text || 'Gráfico DataLab')
        : (TYPE_LABELS[slide.type] || slide.text.substring(0, 18) || '—');

      const ex = Math.max(0, Math.min(cx + slide.x / divisor - SW/2, cw - SW));
      const ey = Math.max(0, Math.min(cy + slide.y / divisor - SH/2, ch - SH));
      el.style.left = ex + 'px';
      el.style.top  = ey + 'px';

      el.addEventListener('click', () => this._selectSlide(slide));

      // Drag
      let dragging = false, sx, sy, ox, oy;
      el.addEventListener('mousedown', e => {
        dragging = true; el.classList.add('dragging');
        sx = e.clientX; sy = e.clientY;
        ox = parseInt(el.style.left); oy = parseInt(el.style.top);
        e.preventDefault();
      }, sig);
      document.addEventListener('mousemove', e => {
        if (!dragging) return;
        const nx = Math.max(0, Math.min(ox + e.clientX - sx, cw - SW));
        const ny = Math.max(0, Math.min(oy + e.clientY - sy, ch - SH));
        el.style.left = nx + 'px';
        el.style.top  = ny + 'px';
        // T5: actualizar coords en tiempo real durante drag
        slide.x = Math.round((nx + SW/2 - cx) * divisor);
        slide.y = Math.round((ny + SH/2 - cy) * divisor);
        this._updateStatus();
      }, sig);
      document.addEventListener('mouseup', () => {
        if (!dragging) return;
        dragging = false; el.classList.remove('dragging');
        slide.x = Math.round((parseInt(el.style.left) + SW/2 - cx) * divisor);
        slide.y = Math.round((parseInt(el.style.top)  + SH/2 - cy) * divisor);
        if (this.currentSlide === slide) this._fillPanel();
        this._updateStatus();
        this._saveState();
      }, sig);

      this.el.canvas.appendChild(el);
    });

    // ── Indicador SVG de rotación para el slide seleccionado ──────────
    if (this.currentSlide && this.currentSlide.rotate) {
      const s = this.currentSlide;
      const ex = Math.max(0, Math.min(cx + s.x / divisor - SW/2, cw - SW));
      const ey = Math.max(0, Math.min(cy + s.y / divisor - SH/2, ch - SH));
      const scx = ex + SW / 2;   // centro X del slide
      const scy = ey + SH / 2;   // centro Y del slide
      const deg = s.rotate % 360;

      const svgR = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svgR.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible';
      svgR.setAttribute('width', cw);
      svgR.setAttribute('height', ch);

      // Radio del arco de rotación
      const R = Math.max(SW, SH) * 0.65;
      const rad = (deg - 90) * Math.PI / 180;  // 0° = arriba
      const arcStartX = scx;
      const arcStartY = scy - R;
      const arcEndX   = scx + R * Math.cos(rad);
      const arcEndY   = scy + R * Math.sin(rad);
      const largeArc  = Math.abs(deg) > 180 ? 1 : 0;
      const sweep     = deg >= 0 ? 1 : 0;

      // Arco de referencia (círculo base tenue)
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', scx); circle.setAttribute('cy', scy);
      circle.setAttribute('r', R);
      circle.setAttribute('fill', 'none');
      circle.setAttribute('stroke', 'rgba(215,165,56,0.12)');
      circle.setAttribute('stroke-width', '1');
      circle.setAttribute('stroke-dasharray', '3,3');

      // Arco coloreado que indica el ángulo
      const arc = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      arc.setAttribute('d', `M ${arcStartX} ${arcStartY} A ${R} ${R} 0 ${largeArc} ${sweep} ${arcEndX} ${arcEndY}`);
      arc.setAttribute('fill', 'none');
      arc.setAttribute('stroke', 'rgba(215,165,56,0.55)');
      arc.setAttribute('stroke-width', '2');
      arc.setAttribute('stroke-linecap', 'round');

      // Línea desde centro al punto del arco
      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', scx); line.setAttribute('y1', scy);
      line.setAttribute('x2', arcEndX); line.setAttribute('y2', arcEndY);
      line.setAttribute('stroke', 'rgba(215,165,56,0.40)');
      line.setAttribute('stroke-width', '1');
      line.setAttribute('stroke-dasharray', '3,2');

      // Punto en el extremo del arco
      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', arcEndX); dot.setAttribute('cy', arcEndY);
      dot.setAttribute('r', '3');
      dot.setAttribute('fill', 'rgba(215,165,56,0.7)');

      // Etiqueta de grados
      const lx = scx + (R + 12) * Math.cos(rad);
      const ly = scy + (R + 12) * Math.sin(rad);
      const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      label.setAttribute('x', lx); label.setAttribute('y', ly + 3);
      label.setAttribute('text-anchor', 'middle');
      label.setAttribute('font-size', '9');
      label.setAttribute('fill', 'rgba(215,165,56,0.8)');
      label.setAttribute('font-family', 'Segoe UI, sans-serif');
      label.setAttribute('font-weight', '600');
      label.textContent = `${deg}°`;

      svgR.appendChild(circle);
      svgR.appendChild(arc);
      svgR.appendChild(line);
      svgR.appendChild(dot);
      svgR.appendChild(label);
      this.el.canvas.appendChild(svgR);
    }
  }

  // ── Historial Undo/Redo ───────────────────────────────────────────
  _saveState() {
    const state = JSON.stringify({ slides: this.slides, title: this.title });
    this.history = this.history.slice(0, this.historyIndex + 1);
    this.history.push(state);
    this.historyIndex++;
    // Limitar historial a 100 estados
    if (this.history.length > 100) {
      this.history.shift();
      this.historyIndex--;
    }
  }

  undo() {
    if (this.historyIndex <= 0) return;
    this.historyIndex--;
    this._restoreState(this.history[this.historyIndex]);
  }

  redo() {
    if (this.historyIndex >= this.history.length - 1) return;
    this.historyIndex++;
    this._restoreState(this.history[this.historyIndex]);
  }

  _restoreState(json) {
    const { slides, title } = JSON.parse(json);
    this.slides = slides;
    this.title  = title;
    const prevId = this.currentSlide?.id;
    this.currentSlide = this.slides.find(s => s.id === prevId) || this.slides[0];
    this._renderList();
    this._fillPanel();
    this._renderCanvas();
  }

  // ── Preview con srcdoc (no depende de preview.html externo) ───────
  showPreview() {
    const html = this._buildPresentationHTML(false);
    this.el.previewFrame.srcdoc = html;
    this._openModal(this.el.modalPreview);
    // Mostrar panel de propiedades flotante dentro del modal
    this._attachPropsToPreview();
  }

  // Adjunta/mueve el panel de propiedades al modal de Preview
  _attachPropsToPreview() {
    const modal = this.el.modalPreview;
    const propsPanel = document.querySelector('.properties-panel');
    if (!propsPanel) return;

    // Crear el overlay flotante si no existe
    const modalBody = modal.querySelector('.modal-body') || modal.querySelector('.modal-box');
    let overlay = modalBody.querySelector('#preview-props-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'preview-props-overlay';
      overlay.style.cssText = [
        'position:fixed;top:60px;right:20px;width:220px;',
        'background:var(--bg-secondary);border:1px solid var(--border);',
        'border-radius:var(--radius);box-shadow:0 4px 20px rgba(0,0,0,0.6);',
        'z-index:9999;display:flex;flex-direction:column;max-height:calc(90vh - 80px);',
        'overflow:hidden;transition:opacity 0.2s'
      ].join('');

      // Header con título y botón minimizar
      const header = document.createElement('div');
      header.style.cssText = 'padding:6px 10px;background:rgba(18,16,16,0.6);border-bottom:1px solid rgba(215,165,56,0.15);' +
        'display:flex;align-items:center;justify-content:space-between;flex-shrink:0;cursor:move';
      header.innerHTML = '<span style="font-size:9px;font-weight:700;color:var(--accent);' +
        'text-transform:uppercase;letter-spacing:0.8px">Propiedades</span>' +
        '<button id="btn-preview-props-toggle" style="background:none;border:none;color:var(--text-muted);' +
        'cursor:pointer;font-size:14px;padding:0 2px;line-height:1" title="Minimizar">−</button>';

      // Clonar el contenido de tabs del panel de propiedades
      const tabsEl   = document.querySelector('.prop-tabs');
      const tabConts = document.querySelectorAll('.prop-tab-content');
      const tabsClone = tabsEl ? tabsEl.cloneNode(true) : null;

      const body = document.createElement('div');
      body.id = 'preview-props-body';
      body.style.cssText = 'overflow-y:auto;flex:1;background:transparent';

      if (tabsClone) {
        body.appendChild(tabsClone);
        tabConts.forEach(tc => {
          const cl = tc.cloneNode(true);
          // Cambiar IDs para no duplicar
          cl.id = 'pv-' + tc.id;
          cl.querySelectorAll('[id]').forEach(el => { el.id = 'pv-' + el.id; });
          body.appendChild(cl);
        });
        // Sincronizar tabs del overlay con los originales
        body.querySelectorAll('.prop-tab').forEach(tab => {
          tab.addEventListener('click', () => {
            body.querySelectorAll('.prop-tab').forEach(t => t.classList.remove('active'));
            body.querySelectorAll('.prop-tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const target = body.querySelector('#pv-prop-tab-' + tab.dataset.tab);
            if (target) target.classList.add('active');
          });
        });
      }

      overlay.appendChild(header);
      overlay.appendChild(body);
      // Inyectar en modal-body (que tiene position:relative y no corta con overflow)
      const modalBody = modal.querySelector('.modal-body') || modal.querySelector('.modal-box');
      modalBody.style.position = 'relative';
      modalBody.appendChild(overlay);

      // Toggle minimizar
      document.getElementById('btn-preview-props-toggle').addEventListener('click', () => {
        const isMin = body.style.display === 'none';
        body.style.display = isMin ? '' : 'none';
        document.getElementById('btn-preview-props-toggle').textContent = isMin ? '−' : '+';
      });

      // Drag del overlay (position:fixed — usa coords de ventana)
      let px = 0, py = 0;
      header.addEventListener('mousedown', e => {
        e.preventDefault();
        px = e.clientX; py = e.clientY;
        const rect = overlay.getBoundingClientRect();
        // Fijar top/left en px para que el drag funcione
        overlay.style.right = 'auto';
        overlay.style.left = rect.left + 'px';
        overlay.style.top  = rect.top  + 'px';
        function onDrag(e) {
          const dx = e.clientX - px, dy = e.clientY - py;
          px = e.clientX; py = e.clientY;
          overlay.style.left = (parseInt(overlay.style.left) + dx) + 'px';
          overlay.style.top  = (parseInt(overlay.style.top)  + dy) + 'px';
        }
        document.addEventListener('mousemove', onDrag);
        document.addEventListener('mouseup', () => document.removeEventListener('mousemove', onDrag), { once: true });
      });
    }
    overlay.style.display = 'flex';
    // Reposicionar a esquina superior derecha al reabrir
    overlay.style.right = '20px';
    overlay.style.top   = '60px';
    overlay.style.removeProperty('left');

    // Sincronizar valores del slide activo al overlay
    this._syncPropsToOverlay(overlay);
  }

  _syncPropsToOverlay(overlay) {
    if (!this.currentSlide || !overlay) return;
    const s = this.currentSlide;
    const map = {
      'pv-prop-text':               s.text,
      'pv-prop-x':                  s.x,
      'pv-prop-y':                  s.y,
      'pv-prop-z':                  s.z,
      'pv-prop-rotate':             s.rotate,
      'pv-prop-scale':              s.scale,
      'pv-prop-font-size':          s.fontSize,
      'pv-prop-content-zoom':       s.contentZoom    != null ? s.contentZoom    : 1.0,
      'pv-prop-content-offset-x':   s.contentOffsetX != null ? s.contentOffsetX : 50,
      'pv-prop-content-offset-y':   s.contentOffsetY != null ? s.contentOffsetY : 50,
    };
    Object.entries(map).forEach(([id, val]) => {
      const el = overlay.querySelector('#' + id);
      if (el) el.value = val;
    });
    const colEl = overlay.querySelector('#pv-prop-text-color');
    if (colEl) colEl.value = this._toHex(s.textColor) || '#e0e0e0';

    // Listener en cada campo del overlay: actualizar slide directamente + refresh preview
    overlay.querySelectorAll('input, select, textarea').forEach(el => {
      if (el._pvBound) return;
      el._pvBound = true;
      const handler = () => {
        if (!this.currentSlide) return;
        const s = this.currentSlide;
        // Mapear ID del overlay → propiedad del slide
        const id = el.id;
        if      (id === 'pv-prop-text')           s.text          = el.value;
        else if (id === 'pv-prop-x')              s.x             = parseInt(el.value)       || 0;
        else if (id === 'pv-prop-y')              s.y             = parseInt(el.value)       || 0;
        else if (id === 'pv-prop-z')              s.z             = parseInt(el.value)       || 0;
        else if (id === 'pv-prop-rotate')         s.rotate        = parseInt(el.value)       || 0;
        else if (id === 'pv-prop-scale')          s.scale         = parseFloat(el.value)     || 1;
        else if (id === 'pv-prop-font-family')    s.fontFamily    = el.value;
        else if (id === 'pv-prop-font-size')      s.fontSize      = parseInt(el.value)       || 48;
        else if (id === 'pv-prop-text-color')     s.textColor     = el.value;
        else if (id === 'pv-prop-image-url')           s.imageUrl      = el.value.trim();
        else if (id === 'pv-prop-iframe-url')          s.iframeUrl     = el.value.trim();
        else if (id === 'pv-prop-content-zoom')        s.contentZoom   = parseFloat(el.value) || 1.0;
        else if (id === 'pv-prop-content-offset-x')   s.contentOffsetX = parseFloat(el.value) ?? 50;
        else if (id === 'pv-prop-content-offset-y')   s.contentOffsetY = parseFloat(el.value) ?? 50;
        // NO propagar al panel original — cada campo actualiza directamente el slide
        // (evita que los listeners del panel sobreescriban otras propiedades del slide)
        // Refrescar canvas y preview
        this._renderCanvas();
        this._updateCurrentSlideLabel();
        this._saveState();
        this.el.previewFrame.srcdoc = this._buildPresentationHTML(false);
      };
      el.addEventListener('input',  handler);
      el.addEventListener('change', handler);
    });
  }

  // ── Exportar ──────────────────────────────────────────────────────
  exportPresentation() {
    const name = prompt('Nombre del archivo (sin .html):', this.title.replace(/[^a-z0-9]/gi,'_')) || 'presentacion';
    const html = this._buildPresentationHTML(true);
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name.trim() + '.html';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ── Constructor del HTML de presentación ──────────────────────────
  // FIX PRINCIPAL: todo el texto de usuario pasa por escapeHtml o
  // formatSlideText antes de insertarse en el HTML generado.
  // ── Normaliza unidades de tamaño para el contexto de Impress.js ──────
  // En Impress los .step son display:block sin altura definida, por lo que
  // height:N% = 0. Convertimos % → vw/vh para que siempre funcionen.
  // El usuario puede escribir px, vw, vh, em, rem — esos pasan sin cambio.
  _normalizeUnit(val, axis) {
    if (!val) return axis === 'w' ? '90vw' : '80vh';
    const str = String(val).trim();
    if (str.endsWith('%')) {
      const n = parseFloat(str);
      return axis === 'w' ? `${n}vw` : `${n}vh`;
    }
    return str;
  }

  _buildPresentationHTML(forExport) {
    const srcdocSlides = []; // acumula los HTML de gráficos DataLab
    const slidesHTML = this.slides.map(s => {
      const attrs = [
        `data-x="${s.x}"`,
        `data-y="${s.y}"`,
        s.z      !== 0 ? `data-z="${s.z}"`           : '',
        s.rotate !== 0 ? `data-rotate="${s.rotate}"`  : '',
        s.scale  !== 1 ? `data-scale="${s.scale}"`    : '',
      ].filter(Boolean).join(' ');

      const cls = s.type === 'slide' ? 'step slide' : 'step';

      if (s.type === 'image' && s.imageUrl) {
        const src  = sanitizeForAttr(s.imageUrl);
        const zoom = s.contentZoom    || 1.0;
        const tx   = ((s.contentOffsetX != null ? s.contentOffsetX : 50) - 50);
        const ty   = ((s.contentOffsetY != null ? s.contentOffsetY : 50) - 50);
        // tx/ty en vw/vh: 0 = centrado, +ve = derecha/abajo, -ve = izquierda/arriba
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="display:flex;align-items:center;justify-content:center;width:100vw;height:100vh"><img src="${src}" style="max-width:90vw;max-height:80vh;object-fit:contain;transform:translate(${tx}vw,${ty}vh) scale(${zoom});transform-origin:center center;display:block;flex-shrink:0" alt=""></div>`;
      }
      if (s.type === 'iframe' && s.iframeUrl) {
        const src  = sanitizeForAttr(s.iframeUrl);
        const zoom = s.contentZoom    || 1.0;
        const tx   = ((s.contentOffsetX != null ? s.contentOffsetX : 50) - 50);
        const ty   = ((s.contentOffsetY != null ? s.contentOffsetY : 50) - 50);
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="display:flex;align-items:center;justify-content:center;width:100vw;height:100vh"><div style="width:90vw;height:80vh;flex-shrink:0;transform:translate(${tx}vw,${ty}vh) scale(${zoom});transform-origin:center center"><iframe src="${src}" style="width:100%;height:100%;border:2px solid rgba(168,230,0,.2);border-radius:6px" loading="lazy"></iframe></div></div>`;
      }
      // Slide con HTML embebido desde DataLab (tablas, srcdoc)
      if (s.type === 'iframe' && s._srcdoc) {
        const bodyMatch  = s._srcdoc.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
        const styleMatch = s._srcdoc.match(/<style[^>]*>([\s\S]*?)<\/style>/i);
        const innerHtml  = bodyMatch  ? bodyMatch[1]                      : s._srcdoc;
        const innerStyle = styleMatch ? `<style>${styleMatch[1]}</style>` : '';
        const zoom = s.contentZoom    || 1.0;
        const tx   = ((s.contentOffsetX != null ? s.contentOffsetX : 50) - 50);
        const ty   = ((s.contentOffsetY != null ? s.contentOffsetY : 50) - 50);
        // inline-block: el wrapper se ajusta al contenido natural sin limitarlo
        // transform no afecta el layout del padre — el contenido no se recorta
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="display:flex;align-items:center;justify-content:center;width:100vw;height:100vh"><div style="display:inline-block;transform:translate(${tx}vw,${ty}vh) scale(${zoom});transform-origin:center center">${innerStyle}${innerHtml}</div></div>`;
      }
      // Slide con gráfico Plotly desde DataLab (tipo 'plotly')
      if (s.type === 'plotly' && s._plotlyData) {
        const idx  = srcdocSlides.length;
        const zoom = s.contentZoom    || 1.0;
        const tx   = ((s.contentOffsetX != null ? s.contentOffsetX : 50) - 50);
        const ty   = ((s.contentOffsetY != null ? s.contentOffsetY : 50) - 50);
        srcdocSlides.push({ id: s.id, data: s._plotlyData });
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="display:flex;align-items:center;justify-content:center;width:100vw;height:100vh"><div style="width:90vw;height:80vh;flex-shrink:0;transform:translate(${tx}vw,${ty}vh) scale(${zoom});transform-origin:center center"><div id="plotly-slide-${idx}" style="width:100%;height:100%"></div></div></div>`;
      }
      if (s.type === 'chart') {
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs}><canvas id="c-${escapeHtml(s.id)}" style="width:800px;height:600px"></canvas></div>`;
      }
      if (s.type === 'blackboard') {
        return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="background:#1a2e10;padding:20px;display:flex;align-items:center;justify-content:center"><div style="width:85vw;height:70vh;overflow:auto;border:2px solid rgba(168,230,0,.2);border-radius:6px;background:#1a2e10"><canvas id="bb-${escapeHtml(s.id)}" width="1200" height="2400" style="display:block;cursor:crosshair;background:#1a2e10"></canvas></div></div>`;
      }
      // Texto normal — SANITIZADO
      const style = `font-family:${sanitizeForAttr(s.fontFamily||'sans-serif')};font-size:${parseInt(s.fontSize)||48}px;color:${sanitizeForAttr(s.textColor||'#e0e0e0')}`;
      return `<div id="${escapeHtml(s.id)}" class="${cls}" ${attrs} style="${style}">${formatSlideText(s.text)}</div>`;
    }).join('\n');

    const chartSlides = this.slides.filter(s => s.type === 'chart' && s.charts?.length);
    const bbSlides    = this.slides.filter(s => s.type === 'blackboard');

    return `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>${escapeHtml(this.title)}</title>
<style>
body{background:radial-gradient(#1a1a1a,#0a0a0a);margin:0;overflow:hidden;}
.slide-counter{position:fixed;bottom:16px;right:16px;font:700 14px/1 'Segoe UI',sans-serif;color:#a8e600;background:rgba(0,0,0,.7);padding:6px 12px;border-radius:4px;border:1px solid rgba(168,230,0,.3);z-index:1000;}
.step{opacity:.08;transition:opacity .4s;}
.step.active{opacity:1;}
.step:has(iframe),.step:has(canvas){opacity:.2;}
.step.active:has(iframe),.step.active:has(canvas){opacity:1;}
/* Los .step no recortan su contenido — Impress gestiona el viewport */
.step > *{overflow:visible;}
</style>
</head>
<body>
<div id="impress">${slidesHTML}</div>
<div class="slide-counter" id="counter">1/${this.slides.length}</div>
<script src="https://cdn.jsdelivr.net/gh/impress/impress.js@1.1.0/js/impress.min.js"><\/script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"><\/script>
<script>
(function(){
  var api = impress();
  var steps = document.querySelectorAll('.step');
  var counter = document.getElementById('counter');
  function upd(){ var a=document.querySelector('.step.active'); if(a) counter.textContent=(Array.from(steps).indexOf(a)+1)+'/'+steps.length; }
  document.addEventListener('impress:init', function(){ setTimeout(upd,10); initCharts(); initBoards(); });
  document.addEventListener('impress:stepenter', upd);
  api.init();

  function initCharts(){
    var data=${JSON.stringify(chartSlides.map(s=>({id:s.id,charts:s.charts})))};
    data.forEach(function(s){
      var canvas=document.getElementById('c-'+s.id); if(!canvas||!s.charts[0]) return;
      canvas.width=800; canvas.height=600;
      new Chart(canvas, JSON.parse(JSON.stringify(s.charts[0].config)));
    });
  }

  function initBoards(){
    var data=${JSON.stringify(bbSlides.map(s=>({id:s.id,bd:s.blackboardData})))};
    data.forEach(function(s){
      var canvas=document.getElementById('bb-'+s.id); if(!canvas) return;
      var ctx=canvas.getContext('2d'), drawing=false, color='#e0e0e0', size=4;
      if(s.bd){ var img=new Image(); img.onload=function(){ctx.drawImage(img,0,0);}; img.src=s.bd; }
      canvas.addEventListener('mousedown',function(e){drawing=true;var r=canvas.getBoundingClientRect();ctx.beginPath();ctx.moveTo((e.clientX-r.left)*(canvas.width/r.width),(e.clientY-r.top)*(canvas.height/r.height));e.preventDefault();});
      canvas.addEventListener('mousemove',function(e){if(!drawing)return;var r=canvas.getBoundingClientRect();ctx.lineWidth=size;ctx.lineCap='round';ctx.strokeStyle=color;ctx.lineTo((e.clientX-r.left)*(canvas.width/r.width),(e.clientY-r.top)*(canvas.height/r.height));ctx.stroke();ctx.beginPath();ctx.moveTo((e.clientX-r.left)*(canvas.width/r.width),(e.clientY-r.top)*(canvas.height/r.height));e.preventDefault();});
      canvas.addEventListener('mouseup',function(){drawing=false;});
      document.addEventListener('keydown',function(e){var m={'1':'#e0e0e0','2':'#a8e600','3':'#ffeb3b','4':'#f48fb1','5':'#81d4fa'};if(m[e.key])color=m[e.key];if(e.key==='+'||e.key==='=')size=Math.min(20,size+2);if(e.key==='-')size=Math.max(2,size-2);});
    });
  }

  // Renderizar graficos Plotly y tablas HTML desde DataLab
  function initSrcdocSlides(){
    var srcdocData=${JSON.stringify(srcdocSlides.map(function(s,i){return{idx:i,data:s.data||null,html:s.html||null,isHtml:s.isHtml||false};}))};
    if(!srcdocData.length) return;

    // Tablas HTML via srcdoc (asignacion JS directa)
    srcdocData.filter(function(i){return i.isHtml;}).forEach(function(item){
      var frame=document.getElementById('iframe-srcdoc-'+item.idx);
      if(frame && item.html){ frame.srcdoc=item.html; }
    });

    // Graficos Plotly (renderizado nativo)
    var plotlyItems=srcdocData.filter(function(i){return !i.isHtml && i.data;});
    if(!plotlyItems.length) return;
    function renderPlotly(){
      plotlyItems.forEach(function(item){
        var el=document.getElementById('plotly-slide-'+item.idx);
        if(!el || !window.Plotly) return;
        var fig = typeof item.data === 'string' ? JSON.parse(item.data) : item.data;
        var layout = fig.layout || {};
        layout.paper_bgcolor='#1a1a1a'; layout.plot_bgcolor='#1a1a1a';
        layout.font={color:'#e0e0e0'}; layout.autosize=true;
        layout.margin=layout.margin||{t:40,r:20,b:50,l:60};
        Plotly.newPlot(el, fig.data||[], layout, {responsive:true,displayModeBar:false});
      });
    }
    if(window.Plotly){ renderPlotly(); }
    else {
      var s=document.createElement('script');
      s.src='https://cdn.plot.ly/plotly-2.32.0.min.js';
      s.onload=renderPlotly;
      document.head.appendChild(s);
    }
  }
  initSrcdocSlides();
})();
<\/script>
</body>
</html>`;
  }

  // ── Pizarra ───────────────────────────────────────────────────────
  _openBlackboard() {
    const ctx = this.el.bbCanvas.getContext('2d');
    ctx.clearRect(0, 0, this.el.bbCanvas.width, this.el.bbCanvas.height);
    if (this.currentSlide?.blackboardData) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0);
      img.src = this.currentSlide.blackboardData;
    }
    this._initBoardEvents();
    this._openModal(this.el.modalBlackboard);
  }

  _initBoardEvents() {
    if (this._boardAbort) this._boardAbort.abort();
    this._boardAbort = new AbortController();
    const sig = { signal: this._boardAbort.signal };
    const canvas = this.el.bbCanvas;
    const ctx = canvas.getContext('2d');
    let drawing = false;
    const getColor = () => {
      const btn = document.querySelector('.btn-chalk.active[data-color]');
      return btn?.dataset.color || '#e0e0e0';
    };
    const getSize = () => parseInt(this.el.chalkSize.value) || 4;

    canvas.addEventListener('mousedown', e => {
      drawing = true;
      const r = canvas.getBoundingClientRect();
      ctx.beginPath();
      ctx.moveTo((e.clientX - r.left) * (canvas.width / r.width), (e.clientY - r.top) * (canvas.height / r.height));
      e.preventDefault();
    }, sig);
    canvas.addEventListener('mousemove', e => {
      if (!drawing) return;
      const r = canvas.getBoundingClientRect();
      const x = (e.clientX - r.left) * (canvas.width / r.width);
      const y = (e.clientY - r.top)  * (canvas.height / r.height);
      const color = getColor();
      ctx.lineWidth = getSize();
      ctx.lineCap = 'round';
      if (color === 'erase') {
        ctx.globalCompositeOperation = 'destination-out';
        ctx.strokeStyle = 'rgba(0,0,0,1)';
      } else {
        ctx.globalCompositeOperation = 'source-over';
        ctx.strokeStyle = color;
      }
      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y);
      e.preventDefault();
    }, sig);
    canvas.addEventListener('mouseup', () => { drawing = false; ctx.globalCompositeOperation = 'source-over'; }, sig);
    canvas.addEventListener('mouseleave', () => { drawing = false; }, sig);
  }

  _clearBoard() {
    const ctx = this.el.bbCanvas.getContext('2d');
    ctx.clearRect(0, 0, this.el.bbCanvas.width, this.el.bbCanvas.height);
  }

  _saveBlackboard() {
    if (this.currentSlide) {
      this.currentSlide.blackboardData = this.el.bbCanvas.toDataURL('image/png');
      this._saveState();
    }
    this._closeModal(this.el.modalBlackboard);
  }

  // ── Gráficos desde Excel ──────────────────────────────────────────
  _handleChartFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const wb = XLSX.read(new Uint8Array(ev.target.result), { type: 'array' });
        this._workbook   = wb;
        this._sheetData  = {};
        this.el.chartSheet.innerHTML = '';
        wb.SheetNames.forEach(name => {
          this._sheetData[name] = XLSX.utils.sheet_to_json(wb.Sheets[name], { header: 1 });
          const opt = document.createElement('option');
          opt.value = opt.textContent = name;
          this.el.chartSheet.appendChild(opt);
        });
        if (wb.SheetNames.length) this._populateColumns(wb.SheetNames[0]);
        this._updateChartModalControls();
        this._openModal(this.el.modalChart);
      } catch(err) {
        alert('Error al leer el archivo Excel: ' + err.message);
      }
    };
    reader.readAsArrayBuffer(file);
  }

  _populateColumns(sheet) {
    const data = this._sheetData[sheet];
    this.el.chartColumns.innerHTML = '';
    this.el.chartXVar.innerHTML    = '';
    if (!data || !data.length) return;
    const headers = data[0].filter(h => h != null && h !== '');
    headers.forEach((h, i) => {
      const label = document.createElement('label');
      const cb = document.createElement('input');
      cb.type = 'checkbox'; cb.value = i; cb.dataset.header = String(h);
      cb.style.accentColor = 'var(--accent)';
      label.appendChild(cb);
      label.appendChild(document.createTextNode(' ' + escapeHtml(String(h))));
      this.el.chartColumns.appendChild(label);

      const opt = document.createElement('option');
      opt.value = i; opt.textContent = String(h);
      this.el.chartXVar.appendChild(opt);
    });
  }

  _updateChartModalControls() {
    const t = this.el.chartType.value;
    const showXAxis = ['bar','line'].includes(t);
    this.el.grpXType.style.display = showXAxis ? 'block' : 'none';
    this.el.grpXVar.style.display  = showXAxis ? 'block' : 'none';
  }

  _generateChart() {
    const sheet   = this.el.chartSheet.value;
    const type    = this.el.chartType.value;
    const records = this.el.chartRecords.value;
    const data    = this._sheetData[sheet];
    if (!data || data.length < 2) { alert('No hay suficientes datos'); return; }

    const checkedCols = Array.from(this.el.chartColumns.querySelectorAll('input:checked'))
      .map(cb => ({ idx: parseInt(cb.value), header: cb.dataset.header }));
    if (!checkedCols.length) { alert('Selecciona al menos una columna'); return; }

    const palette = COLOR_PALETTES[this.el.palette?.value || 'default'];
    const limit   = records === 'all' ? data.length : Math.min(parseInt(records)+1, data.length);
    const rows    = data.slice(1, limit);

    let labels, datasets;
    if (['bar','line'].includes(type)) {
      const xi = parseInt(this.el.chartXVar.value);
      labels   = rows.map(r => String(r[xi] ?? ''));
      datasets = checkedCols.map((col, i) => ({
        label:           col.header,
        data:            rows.map(r => parseFloat(r[col.idx]) || 0),
        backgroundColor: palette.bg[i % palette.bg.length],
        borderColor:     palette.border[i % palette.border.length],
        borderWidth:     2,
      }));
    } else if (type === 'pie') {
      labels   = rows.map((_, i) => String(i + 1));
      datasets = checkedCols.slice(0,1).map(col => ({
        label:           col.header,
        data:            rows.map(r => parseFloat(r[col.idx]) || 0),
        backgroundColor: palette.bg,
        borderColor:     palette.border,
        borderWidth:     1,
      }));
    } else { // scatter
      const xi = parseInt(this.el.chartXVar.value);
      labels   = [];
      datasets = checkedCols.map((col, i) => ({
        label:           col.header,
        data:            rows.map(r => ({ x: parseFloat(r[xi])||0, y: parseFloat(r[col.idx])||0 })),
        backgroundColor: palette.bg[i % palette.bg.length],
        borderColor:     palette.border[i % palette.border.length],
        borderWidth:     2,
      }));
    }

    if (!this.currentSlide) return;
    this.currentSlide.charts = [{
      id:     'chart-' + Date.now(),
      config: {
        type, data: { labels, datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#e0e0e0' } } },
          scales: type !== 'pie' ? {
            x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,.08)' } },
            y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,.08)' } }
          } : {}
        }
      }
    }];
    this._saveState();
    this._renderCanvas();
    this._closeModal(this.el.modalChart);
    this.el.chartFile.value = '';
  }

  // ── Cargar presentación HTML existente ────────────────────────────
  loadPresentation(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(ev.target.result, 'text/html');
        const steps = doc.querySelectorAll('#impress .step');
        if (!steps.length) { alert('No se encontraron slides en el archivo'); return; }
        this.slides = Array.from(steps).map((el, i) => this._newSlide({
          id:        el.id || `imported-${i}`,
          text:      el.textContent.trim().substring(0, 200),
          x:         parseInt(el.dataset.x)      || 0,
          y:         parseInt(el.dataset.y)       || 0,
          z:         parseInt(el.dataset.z)       || 0,
          rotate:    parseInt(el.dataset.rotate)  || 0,
          scale:     parseFloat(el.dataset.scale) || 1,
          type:      el.querySelector('iframe') ? 'iframe' : el.querySelector('img') ? 'image' : el.querySelector('canvas') ? 'chart' : 'slide',
          imageUrl:  el.querySelector('img')?.src    || '',
          iframeUrl: el.querySelector('iframe')?.src || '',
        }));
        this.slideCounter = this.slides.length;
        this._renderList();
        this._selectSlide(this.slides[0]);
        this._saveState();
      } catch(err) {
        alert('Error al cargar: ' + err.message);
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  }
}

// ── Bootstrap ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  window._editor = new PresentationEditor();

  // ── T1: Menú ··· ────────────────────────────────────────────────
  var moreBtn  = document.getElementById('btn-more-menu');
  var moreDrop = document.getElementById('more-menu-dropdown');
  if (moreBtn && moreDrop) {
    moreBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      moreDrop.style.display = moreDrop.style.display === 'none' ? 'block' : 'none';
    });
    document.addEventListener('click', function() { if (moreDrop) moreDrop.style.display = 'none'; });
    // Estilo hover items
    moreDrop.querySelectorAll('button').forEach(function(b) {
      b.classList.add('more-menu-item');
      if (b.id === 'btn-clear-slides') b.classList.add('danger');
    });
  }

  // ── T2: Toggle panel izquierdo ───────────────────────────────────
  var toggleBtn = document.getElementById('btn-panel-toggle');
  var editorBody = document.querySelector('.editor-body');
  var collapsed = localStorage.getItem('neven_panel_collapsed') === '1';
  function applyCollapse(c) {
    collapsed = c;
    if (editorBody) editorBody.classList.toggle('panel-collapsed', c);
    if (toggleBtn)  toggleBtn.innerHTML = c ? '&#8250;' : '&#8249;';
    if (toggleBtn)  toggleBtn.title = c ? 'Expandir panel' : 'Colapsar panel';
    localStorage.setItem('neven_panel_collapsed', c ? '1' : '0');
    setTimeout(function() { if (window._editor) window._editor._renderCanvas(); }, 220);
  }
  if (toggleBtn) toggleBtn.addEventListener('click', function() { applyCollapse(!collapsed); });
  applyCollapse(collapsed);

  // ── T3: Tabs del panel de propiedades ────────────────────────────
  document.querySelectorAll('.prop-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      document.querySelectorAll('.prop-tab').forEach(function(t) { t.classList.remove('active'); });
      document.querySelectorAll('.prop-tab-content').forEach(function(c) { c.classList.remove('active'); });
      tab.classList.add('active');
      var target = document.getElementById('prop-tab-' + tab.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // ── T4: Zoom ─────────────────────────────────────────────────────
  window._editor._zoom = parseFloat(localStorage.getItem('neven_zoom') || '1.0');
  function _applyZoom(z) {
    z = Math.max(0.25, Math.min(4.0, Math.round(z * 4) / 4));
    window._editor._zoom = z;
    localStorage.setItem('neven_zoom', z);
    var resetBtn = document.getElementById('btn-zoom-reset');
    if (resetBtn) resetBtn.textContent = Math.round(z * 100) + '%';
    window._editor._renderCanvas();
  }
  var zoomIn    = document.getElementById('btn-zoom-in');
  var zoomOut   = document.getElementById('btn-zoom-out');
  var zoomReset = document.getElementById('btn-zoom-reset');
  if (zoomIn)    zoomIn.addEventListener('click',    function() { _applyZoom(window._editor._zoom + 0.25); });
  if (zoomOut)   zoomOut.addEventListener('click',   function() { _applyZoom(window._editor._zoom - 0.25); });
  if (zoomReset) zoomReset.addEventListener('click', function() { _applyZoom(1.0); });
  _applyZoom(window._editor._zoom);
});

// ── Receptor de gráficos desde DataLab ────────────────────────────
// Escucha mensajes de tipo NEVEN_ADD_SLIDE enviados por datalab.js
// via el relay en taskpane.html.
window.addEventListener('message', function(event) {
  if (event.origin !== window.location.origin) return;
  if (!event.data || event.data.type !== 'NEVEN_ADD_SLIDE') return;

  var editor = window._editor;
  if (!editor) {
    console.warn('[NEVEN Presentaciones] Editor no inicializado aún');
    return;
  }

  var slideHtml  = event.data.slideHtml  || '';
  var slideTitle = event.data.slideTitle || 'Gráfico DataLab';
  var plotlyData = event.data.plotlyData || null;

  // Calcular posición: colocar el nuevo slide a la derecha del último
  var lastX = editor.slides.length
    ? editor.slides[editor.slides.length - 1].x + 1400
    : 0;

  var newSlide;
  if (plotlyData) {
    // Gráfico Plotly desde DataLab — tipo 'plotly' (renderizado nativo)
    newSlide = editor._newSlide({
      text:        slideTitle,
      type:        'plotly',
      _plotlyData: plotlyData,
      x: lastX, y: 0, scale: 1
    });
  } else {
    // Fallback: contenido HTML genérico como iframe srcdoc
    newSlide = editor._newSlide({
      text:      slideTitle,
      type:      'iframe',
      iframeUrl: '',
      _srcdoc:   slideHtml,
      x: lastX, y: 0, scale: 1
    });
  }

  editor.slides.push(newSlide);
  editor._renderList();
  editor._selectSlide(newSlide);
  editor._saveState();

  // Feedback: flash del slide recién creado en la lista
  setTimeout(function() {
    var cards = document.querySelectorAll('.slide-card');
    var last  = cards[cards.length - 1];
    if (last) {
      last.style.transition  = 'background 0.3s';
      last.style.background  = 'rgba(215,165,56,0.35)';
      setTimeout(function() { last.style.background = ''; }, 600);
    }
  }, 50);
});
