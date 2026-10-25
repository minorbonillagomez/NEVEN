// ═══════════════════════════════════════════════════════════════════════════════
// NEVEN Studio — Color Palettes Module
// ═══════════════════════════════════════════════════════════════════════════════
// Sistema centralizado de paletas de colores para gráficos.
// Afecta Quick Plots, Chart Gallery, y cualquier visualización del TaskPane.
// ═══════════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ─── Definición de Paletas ─────────────────────────────────────────────────
  
  const PALETTES = {
    neven: {
      name: { en: 'NEVEN', es: 'NEVEN' },
      colors: ['#d7a538', '#4a9eff', '#50c878', '#ff6b6b', '#9b59b6', '#1abc9c'],
      primary: '#d7a538',
      description: { en: 'Corporate/Professional', es: 'Corporativo/Profesional' }
    },
    viridis: {
      name: { en: 'Viridis', es: 'Viridis' },
      colors: ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'],
      primary: '#21918c',
      description: { en: 'Scientific/Colorblind-safe', es: 'Científico/Accesible' }
    },
    warm: {
      name: { en: 'Warm', es: 'Cálida' },
      colors: ['#d7263d', '#f46036', '#ffd166', '#ee964b', '#f95738'],
      primary: '#f46036',
      description: { en: 'Energetic presentations', es: 'Presentaciones energéticas' }
    },
    cool: {
      name: { en: 'Cool', es: 'Fría' },
      colors: ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51'],
      primary: '#2a9d8f',
      description: { en: 'Nature/Ecology', es: 'Naturaleza/Ecología' }
    },
    pastel: {
      name: { en: 'Pastel', es: 'Pastel' },
      colors: ['#ffadad', '#ffd6a5', '#fdffb6', '#caffbf', '#9bf6ff', '#a0c4ff'],
      primary: '#ffd6a5',
      description: { en: 'Educational/Soft', es: 'Educativo/Suave' }
    },
    ocean: {
      name: { en: 'Ocean', es: 'Océano' },
      colors: ['#03045e', '#0077b6', '#00b4d8', '#90e0ef', '#caf0f8'],
      primary: '#0077b6',
      description: { en: 'Finance/Corporate', es: 'Finanzas/Corporativo' }
    },
    sunset: {
      name: { en: 'Sunset', es: 'Atardecer' },
      colors: ['#f72585', '#7209b7', '#3a0ca3', '#4361ee', '#4cc9f0'],
      primary: '#f72585',
      description: { en: 'Marketing/Impactful', es: 'Marketing/Impactante' }
    },
    earth: {
      name: { en: 'Earth', es: 'Tierra' },
      colors: ['#606c38', '#283618', '#fefae0', '#dda15e', '#bc6c25'],
      primary: '#606c38',
      description: { en: 'Agriculture/Sustainability', es: 'Agricultura/Sostenibilidad' }
    },
    monochrome: {
      name: { en: 'Monochrome', es: 'Monocromático' },
      colors: ['#212529', '#495057', '#6c757d', '#adb5bd', '#dee2e6'],
      primary: '#495057',
      description: { en: 'Formal reports', es: 'Reportes formales' }
    },
    tableau: {
      name: { en: 'Tableau', es: 'Tableau' },
      colors: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948'],
      primary: '#4e79a7',
      description: { en: 'Dashboards', es: 'Dashboards' }
    },
    ibm: {
      name: { en: 'IBM', es: 'IBM' },
      colors: ['#648fff', '#785ef0', '#dc267f', '#fe6100', '#ffb000'],
      primary: '#648fff',
      description: { en: 'Technology/Accessible', es: 'Tecnología/Accesible' }
    },
    retro: {
      name: { en: 'Retro', es: 'Retro' },
      colors: ['#e63946', '#f1faee', '#a8dadc', '#457b9d', '#1d3557'],
      primary: '#e63946',
      description: { en: 'Vintage/Editorial', es: 'Vintage/Editorial' }
    }
  };

  // ─── Estado ────────────────────────────────────────────────────────────────
  
  const STORAGE_KEY = 'neven_color_palette';
  let _currentPalette = 'neven';
  let _listeners = [];

  // ─── Funciones Públicas ────────────────────────────────────────────────────

  /**
   * Obtiene la paleta actual
   * @returns {Object} Objeto con colors, primary, name, description
   */
  function getCurrentPalette() {
    return PALETTES[_currentPalette] || PALETTES.neven;
  }

  /**
   * Obtiene el ID de la paleta actual
   * @returns {string} ID de la paleta (ej: 'neven', 'viridis')
   */
  function getCurrentPaletteId() {
    return _currentPalette;
  }

  /**
   * Obtiene todas las paletas disponibles
   * @returns {Object} Objeto con todas las paletas
   */
  function getAllPalettes() {
    return PALETTES;
  }

  /**
   * Cambia la paleta actual
   * @param {string} paletteId - ID de la paleta
   */
  function setPalette(paletteId) {
    if (!PALETTES[paletteId]) {
      console.warn(`[ColorPalettes] Unknown palette: ${paletteId}`);
      return;
    }
    
    _currentPalette = paletteId;
    
    // Persistir en localStorage
    try {
      localStorage.setItem(STORAGE_KEY, paletteId);
    } catch (e) {
      console.warn('[ColorPalettes] Could not save to localStorage:', e);
    }
    
    // Actualizar window.ANYPLOT_TOKENS para Chart Gallery
    updateAnyplotTokens();
    
    // Notificar a listeners
    _listeners.forEach(fn => {
      try { fn(getCurrentPalette(), paletteId); } catch (e) { console.error(e); }
    });
    
    console.log(`[ColorPalettes] Palette changed to: ${paletteId}`);
  }

  /**
   * Registra un listener para cambios de paleta
   * @param {Function} callback - Función a llamar cuando cambie la paleta
   * @returns {Function} Función para desregistrar el listener
   */
  function onPaletteChange(callback) {
    _listeners.push(callback);
    return () => {
      _listeners = _listeners.filter(fn => fn !== callback);
    };
  }

  /**
   * Obtiene el color primario actual
   * @returns {string} Color hex (ej: '#d7a538')
   */
  function getPrimaryColor() {
    return getCurrentPalette().primary;
  }

  /**
   * Obtiene el array de colores actual
   * @returns {string[]} Array de colores hex
   */
  function getColors() {
    return getCurrentPalette().colors;
  }

  /**
   * Obtiene un color por índice (con wrap-around)
   * @param {number} index - Índice del color
   * @returns {string} Color hex
   */
  function getColor(index) {
    const colors = getColors();
    return colors[index % colors.length];
  }

  /**
   * Genera versión con alpha del color primario
   * @param {number} alpha - Valor de alpha (0-1)
   * @returns {string} Color rgba
   */
  function getPrimaryRgba(alpha = 0.7) {
    const hex = getPrimaryColor();
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  /**
   * Genera colorscale para Plotly (gradiente de oscuro a color primario)
   * @returns {Array} Colorscale para Plotly
   */
  function getPlotlyColorscale() {
    const primary = getPrimaryColor();
    return [[0, '#1a1a1a'], [0.5, '#444'], [1, primary]];
  }

  /**
   * Actualiza window.ANYPLOT_TOKENS con la paleta actual
   */
  function updateAnyplotTokens() {
    const palette = getCurrentPalette();
    window.ANYPLOT_TOKENS = {
      pageBg: '#1e1e1e',
      elevatedBg: '#2d2d2d',
      ink: '#e0e0e0',
      inkSoft: '#a0a0a0',
      grid: '#404040',
      amber: palette.primary,
      palette: palette.colors
    };
    
    // También actualizar ANYPLOT_SIZE si no existe
    if (!window.ANYPLOT_SIZE) {
      window.ANYPLOT_SIZE = { width: 800, height: 400 };
    }
  }

  // ─── Inicialización ────────────────────────────────────────────────────────

  function init() {
    // Cargar paleta guardada
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && PALETTES[saved]) {
        _currentPalette = saved;
      }
    } catch (e) {
      console.warn('[ColorPalettes] Could not load from localStorage:', e);
    }
    
    // Inicializar ANYPLOT_TOKENS
    updateAnyplotTokens();
    
    console.log(`[ColorPalettes] Initialized with palette: ${_currentPalette}`);
  }

  // ─── API Pública ───────────────────────────────────────────────────────────

  window.ColorPalettes = {
    // Getters
    getCurrentPalette,
    getCurrentPaletteId,
    getAllPalettes,
    getPrimaryColor,
    getColors,
    getColor,
    getPrimaryRgba,
    getPlotlyColorscale,
    
    // Setters
    setPalette,
    
    // Events
    onPaletteChange,
    
    // Utils
    updateAnyplotTokens,
    
    // Constants
    PALETTES
  };

  // Auto-init
  init();

})();
