// ═══════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Sistema de Internacionalización (i18n)
// ═══════════════════════════════════════════════════════════════════════════
// Archivo: lang/i18n.js
// Descripción: Funciones para aplicar idioma dinámicamente al TaskPane
// ═══════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ─────────────────────────────────────────────────────────────────────────
  // CONFIGURACIÓN
  // ─────────────────────────────────────────────────────────────────────────
  const STORAGE_KEY = 'neven-lang';
  const DEFAULT_LANG = 'es';
  const SUPPORTED_LANGS = ['es', 'en'];

  // ─────────────────────────────────────────────────────────────────────────
  // ESTADO GLOBAL
  // ─────────────────────────────────────────────────────────────────────────
  let currentLang = DEFAULT_LANG;
  let dictionaries = {};

  // ─────────────────────────────────────────────────────────────────────────
  // FUNCIONES UTILITARIAS
  // ─────────────────────────────────────────────────────────────────────────
  
  /**
   * Obtiene un valor anidado de un objeto usando notación de punto
   * @param {Object} obj - Objeto fuente
   * @param {string} path - Ruta con puntos (ej: "tabs.dataStudio")
   * @returns {string|undefined} - Valor encontrado o undefined
   */
  function getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  }

  /**
   * Registra un diccionario de idioma
   * @param {string} langCode - Código del idioma (es, en)
   * @param {Object} dictionary - Diccionario de traducciones
   */
  function registerDictionary(langCode, dictionary) {
    dictionaries[langCode] = dictionary;
  }

  /**
   * Obtiene el idioma actual
   * @returns {string} - Código del idioma actual
   */
  function getCurrentLang() {
    return currentLang;
  }

  /**
   * Obtiene el diccionario actual
   * @returns {Object} - Diccionario del idioma actual
   */
  function getCurrentDictionary() {
    return dictionaries[currentLang] || dictionaries[DEFAULT_LANG] || {};
  }

  /**
   * Traduce una clave
   * @param {string} key - Clave de traducción (ej: "buttons.run")
   * @param {Object} [params] - Parámetros para interpolación (opcional)
   * @returns {string} - Texto traducido o la clave si no se encuentra
   */
  function t(key, params) {
    const dict = getCurrentDictionary();
    let text = getNestedValue(dict, key);
    
    if (text === undefined) {
      console.warn('[i18n] Missing translation:', key);
      return key;
    }

    // Interpolación simple: {{variable}}
    if (params && typeof text === 'string') {
      Object.keys(params).forEach(param => {
        text = text.replace(new RegExp('{{' + param + '}}', 'g'), params[param]);
      });
    }

    return text;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // APLICACIÓN DEL IDIOMA
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Aplica el idioma seleccionado a todos los elementos con data-i18n
   * @param {string} langCode - Código del idioma (es, en)
   */
  function applyLanguage(langCode) {
    if (!SUPPORTED_LANGS.includes(langCode)) {
      console.warn('[i18n] Unsupported language:', langCode);
      langCode = DEFAULT_LANG;
    }

    if (!dictionaries[langCode]) {
      console.error('[i18n] Dictionary not loaded:', langCode);
      return;
    }

    currentLang = langCode;
    const dict = dictionaries[langCode];

    // Aplicar a elementos con data-i18n (contenido de texto)
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = getNestedValue(dict, key);
      if (text !== undefined) {
        el.textContent = text;
      }
    });

    // Aplicar a elementos con data-i18n-placeholder (placeholder de inputs)
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const text = getNestedValue(dict, key);
      if (text !== undefined) {
        el.placeholder = text;
      }
    });

    // Aplicar a elementos con data-i18n-title (atributo title/tooltip)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const text = getNestedValue(dict, key);
      if (text !== undefined) {
        el.title = text;
      }
    });

    // Aplicar a elementos con data-i18n-value (value de options)
    document.querySelectorAll('[data-i18n-value]').forEach(el => {
      const key = el.getAttribute('data-i18n-value');
      const text = getNestedValue(dict, key);
      if (text !== undefined) {
        el.textContent = text;
      }
    });

    // ═══════════════════════════════════════════════════════════════════════
    // TRADUCCIONES ESPECÍFICAS POR ID (para elementos con SVG u otros hijos)
    // ═══════════════════════════════════════════════════════════════════════
    const specificTranslations = {
      // Data Studio - botones principales
      'btn-load': { key: 'buttons.openFile', textNode: true },
      'btn-bridge-read': { key: 'buttons.readFromExcel', textNode: true },
      'btn-paste-excel': { key: 'buttons.pasteFromExcel', textNode: true },
      'btn-db-connect': { key: 'buttons.connectDB', textNode: true },
      'btn-pivot': { key: 'buttons.openPivot', textNode: false },
      
      // Data Studio - textos
      'data-info': { key: 'dataStudio.openFileHint', textNode: false },
      
      // Quick Chart
      'btn-qc-generate': { key: 'dataStudio.generateChart', textNode: true },
      
      // Run Script - botones
      'btn-run-script': { key: 'buttons.run', textNode: true },
      'btn-new-script': { key: 'buttons.newScript', textNode: true },
      
      // Data Lab
      'dl-run-btn': { key: 'dataLab.runAnalysis', textNode: false },
      
      // Econometría
      'btn-econometria-run': { key: 'buttons.run', textNode: true }
    };

    Object.entries(specificTranslations).forEach(([id, config]) => {
      const el = document.getElementById(id);
      if (!el) return;
      
      const text = getNestedValue(dict, config.key);
      if (text === undefined) return;

      if (config.textNode) {
        // Buscar el nodo de texto después del SVG
        const textNodes = Array.from(el.childNodes).filter(n => n.nodeType === Node.TEXT_NODE);
        if (textNodes.length > 0) {
          textNodes[textNodes.length - 1].textContent = ' ' + text;
        }
      } else {
        el.textContent = text;
      }
    });

    // ═══════════════════════════════════════════════════════════════════════
    // TRADUCCIONES DE SELECTS (optgroups y options)
    // ═══════════════════════════════════════════════════════════════════════
    
    // Quick Chart - tipos de gráfico
    const qcType = document.getElementById('qc-type');
    if (qcType) {
      const chartTypeTranslations = dict.dataStudio?.chartTypes || {};
      const optgroupLabels = {
        'Basicos': langCode === 'en' ? 'Basic' : 'Básicos',
        'Estadisticos': langCode === 'en' ? 'Statistical' : 'Estadísticos',
        'Series de Tiempo': langCode === 'en' ? 'Time Series' : 'Series de Tiempo',
        'Geoespacial': langCode === 'en' ? 'Geospatial' : 'Geoespacial',
        'Avanzados': langCode === 'en' ? 'Advanced' : 'Avanzados'
      };
      
      qcType.querySelectorAll('optgroup').forEach(og => {
        const currentLabel = og.label;
        if (optgroupLabels[currentLabel]) {
          og.label = optgroupLabels[currentLabel];
        }
      });
      
      qcType.querySelectorAll('option').forEach(opt => {
        const val = opt.value;
        if (chartTypeTranslations[val]) {
          // Preservar emoji si existe
          const emoji = opt.textContent.match(/^[^\w\s]/)?.[0] || '';
          opt.textContent = emoji ? emoji + ' ' + chartTypeTranslations[val] : chartTypeTranslations[val];
        }
      });
    }

    // Selector de lenguaje en Run Script
    const scriptLang = document.getElementById('script-lang');
    if (scriptLang) {
      // Los nombres de lenguajes (R, Python, Julia, SQL) son universales, no necesitan traducción
    }

    // Selector de ejemplos en Run Script
    const scriptExamples = document.getElementById('script-examples');
    if (scriptExamples) {
      const examplesLabel = langCode === 'en' ? 'Examples...' : 'Ejemplos...';
      const firstOption = scriptExamples.querySelector('option[value=""]');
      if (firstOption) firstOption.textContent = examplesLabel;
      
      // Traducir labels de optgroups
      const exampleGroups = dict.runScript?.exampleGroups || {};
      scriptExamples.querySelectorAll('optgroup').forEach(og => {
        const currentLabel = og.label;
        if (currentLabel === 'R' || currentLabel === 'Python' || currentLabel === 'Julia') {
          // Estos no cambian
        } else if (currentLabel.includes('SQL')) {
          og.label = exampleGroups.sql || currentLabel;
        }
      });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // TRADUCCIONES DE CARD TITLES (por clase y contenido)
    // ═══════════════════════════════════════════════════════════════════════
    const cardTitleTranslations = {
      'Datos': 'dataStudio.title',
      'Gráfico Rápido': 'dataStudio.quickChart',
      'Grafico Rapido': 'dataStudio.quickChart',
      'Data Lab': 'tabs.dataLab',
      'Output': 'labels.output',
      'Configuración General': 'settings.title',
      'General Settings': 'settings.title'
    };

    document.querySelectorAll('.card-title').forEach(el => {
      const currentText = el.textContent.trim();
      const key = cardTitleTranslations[currentText];
      if (key) {
        const text = getNestedValue(dict, key);
        if (text) el.textContent = text;
      }
    });

    // ═══════════════════════════════════════════════════════════════════════
    // TRADUCCIONES DE PLACEHOLDERS (por ID de input)
    // ═══════════════════════════════════════════════════════════════════════
    const placeholderTranslations = {
      'func-search': langCode === 'en' ? 'Search...' : 'Buscar...',
      'ayuda-search': langCode === 'en' ? 'Search function by name or description...' : 'Buscar función por nombre o descripción...',
      'ai-input': langCode === 'en' ? 'Type your question... (Enter sends, Shift+Enter new line)' : 'Escribe tu pregunta... (Enter envía, Shift+Enter nueva línea)',
      'graph-entity-search': langCode === 'en' ? 'Search entity (e.g., OLS, GARCH, regression)' : 'Buscar entidad (ej: OLS, GARCH, regression)',
      'dl-filter-input': langCode === 'en' ? 'e.g., age > 18 AND country = \'US\'' : 'Ej: edad > 18 AND pais = \'CR\'',
      'rag-query-input': langCode === 'en' ? 'Type your question...' : 'Escribe tu pregunta...',
      'rag-text-content': langCode === 'en' ? 'Paste or type content here...' : 'Pega o escribe el contenido aquí...',
      'rag-text-name': langCode === 'en' ? 'Document name' : 'Nombre del documento',
      'rag-file-path': langCode === 'en' ? 'Path to file...' : 'Ruta al archivo...'
    };

    Object.entries(placeholderTranslations).forEach(([id, placeholder]) => {
      const el = document.getElementById(id);
      if (el) el.placeholder = placeholder;
    });

    // Guardar preferencia
    try {
      localStorage.setItem(STORAGE_KEY, langCode);
    } catch (e) {
      // localStorage no disponible (ej: modo privado)
    }

    // Actualizar selector de idioma si existe
    const langSelector = document.getElementById('lang-selector');
    if (langSelector) {
      langSelector.value = langCode;
    }

    // Disparar evento personalizado
    document.dispatchEvent(new CustomEvent('languageChanged', { 
      detail: { language: langCode }
    }));

    console.log('[i18n] Language applied:', langCode);
  }

  /**
   * Inicializa el sistema i18n
   * - Registra diccionarios si están disponibles globalmente
   * - Aplica el idioma guardado o el predeterminado
   */
  function init() {
    // Registrar diccionarios si están disponibles
    if (window.LANG_ES) registerDictionary('es', window.LANG_ES);
    if (window.LANG_EN) registerDictionary('en', window.LANG_EN);

    // Obtener idioma guardado o usar predeterminado
    let savedLang = DEFAULT_LANG;
    try {
      savedLang = localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG;
    } catch (e) {
      // localStorage no disponible
    }

    // Aplicar idioma
    if (dictionaries[savedLang]) {
      applyLanguage(savedLang);
    } else {
      applyLanguage(DEFAULT_LANG);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // TRADUCCIÓN DE FUNCIONES DATA LAB
  // ─────────────────────────────────────────────────────────────────────────
  
  /**
   * Traduce una FunctionCard de Data Lab
   * @param {Object} card - Card con id, name, description del catálogo
   * @returns {Object} - {name, description} traducidos al idioma actual
   */
  function translateCard(card) {
    if (!card || !card.id) return { name: card?.name || '', description: card?.description || '' };
    
    const dict = getCurrentDictionary();
    const funcTranslations = dict.dataLab?.functions?.[card.id];
    
    if (funcTranslations) {
      return {
        name: funcTranslations.name || card.name,
        description: funcTranslations.description || card.description || ''
      };
    }
    
    // Fallback al contenido original del catálogo
    return {
      name: card.name || card.id,
      description: card.description || ''
    };
  }

  /**
   * Re-aplica traducciones a elementos dinámicos de Data Lab
   * Llamar después de renderizar la lista de funciones
   */
  function translateDataLabUI() {
    const dict = getCurrentDictionary();
    const lang = currentLang;
    
    // Traducir dropdown de familias
    const familySelect = document.getElementById('dl-family-select');
    if (familySelect) {
      const firstOption = familySelect.querySelector('option[value=""]');
      if (firstOption) {
        firstOption.textContent = dict.dataLab?.selectFamily || 
          (lang === 'en' ? '-- Select a family --' : '-- Seleccione una familia --');
      }
    }
    
    // Traducir card de descripción (título y botón Wikipedia)
    const descCardTitle = document.querySelector('#dl-desc-card .card-title');
    if (descCardTitle) {
      descCardTitle.textContent = dict.dataLab?.aboutMethod || 
        (lang === 'en' ? 'About this method' : 'Sobre este método');
    }
    
    const wikiBtn = document.querySelector('#dl-desc-card a.btn');
    if (wikiBtn) {
      wikiBtn.innerHTML = dict.dataLab?.goToWikipedia || 
        (lang === 'en' ? '🌐 Go to Wikipedia' : '🌐 Ir a Wikipedia');
    }
    
    // Traducir botón "Ejecutar análisis"
    const runBtn = document.getElementById('dl-run-btn');
    if (runBtn) {
      runBtn.textContent = dict.dataLab?.runAnalysis || 
        (lang === 'en' ? 'Run Analysis' : 'Ejecutar análisis');
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  // API PÚBLICA
  // ─────────────────────────────────────────────────────────────────────────
  window.i18n = {
    init: init,
    applyLanguage: applyLanguage,
    t: t,
    getCurrentLang: getCurrentLang,
    getCurrentDictionary: getCurrentDictionary,
    registerDictionary: registerDictionary,
    translateCard: translateCard,
    translateDataLabUI: translateDataLabUI,
    SUPPORTED_LANGS: SUPPORTED_LANGS,
    DEFAULT_LANG: DEFAULT_LANG
  };

  // Auto-inicializar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM ya está listo
    init();
  }

})();
