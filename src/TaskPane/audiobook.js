/**
 * NEVEN Studio - Audiobook Tab Handler
 * Maneja la interfaz de generación de audiolibros M4B
 * 
 * Puerto del servidor: 5556 (separado del servidor principal en 5555)
 * @version 1.0.0
 * @date 2026-08-19
 */

(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFIGURACIÓN
  // ═══════════════════════════════════════════════════════════════════════════
  
  const AUDIOBOOK_PORT = 5556;
  const AUDIOBOOK_API_BASE = `http://localhost:${AUDIOBOOK_PORT}`;
  
  // Estado global del módulo
  const state = {
    serverOnline: false,
    selectedFile: null,
    conversionInProgress: false,
    lastResult: null,
    pollInterval: null
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // UTILIDADES
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Muestra un toast temporal (reutiliza showToast global si existe)
   */
  function showToast(message, duration = 3000) {
    if (typeof window.showToast === 'function') {
      window.showToast(message, duration);
    } else {
      console.log('[Audiobook]', message);
    }
  }

  /**
   * Formatea bytes a tamaño legible
   */
  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  /**
   * Formatea duración en segundos a HH:MM:SS
   */
  function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return 'N/A';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
      return `${h}h ${m}m ${s}s`;
    }
    return `${m}m ${s}s`;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // VERIFICACIÓN DEL SERVIDOR
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Verifica si el servidor de audiobook está corriendo
   */
  async function checkServerStatus() {
    const dot = document.getElementById('audiobook-server-dot');
    const text = document.getElementById('audiobook-server-text');
    const startBtn = document.getElementById('btn-audiobook-start-server');
    const convertBtn = document.getElementById('btn-audiobook-convert');

    try {
      const response = await fetch(`${AUDIOBOOK_API_BASE}/api/health`, {
        method: 'GET',
        mode: 'cors',
        timeout: 3000
      });
      
      if (response.ok) {
        const data = await response.json();
        state.serverOnline = true;
        
        dot.style.background = '#27ae60';
        text.textContent = `Servidor activo v${data.version || '0.1.0'}`;
        text.style.color = '#27ae60';
        startBtn.style.display = 'none';
        
        // Habilitar conversión si hay archivo seleccionado
        if (state.selectedFile) {
          convertBtn.disabled = false;
        }
        
        return true;
      }
    } catch (e) {
      // Servidor no disponible
    }
    
    state.serverOnline = false;
    dot.style.background = '#e74c3c';
    text.textContent = 'Servidor no disponible';
    text.style.color = '#e74c3c';
    startBtn.style.display = 'inline-block';
    convertBtn.disabled = true;
    
    return false;
  }

  /**
   * Intenta iniciar el servidor de audiobook
   */
  async function startServer() {
    const startBtn = document.getElementById('btn-audiobook-start-server');
    const text = document.getElementById('audiobook-server-text');
    
    startBtn.disabled = true;
    text.textContent = 'Iniciando servidor...';
    
    try {
      // Intentar iniciar via el servidor principal de NEVEN
      const response = await fetch('http://localhost:5555/api/audiobook/start', {
        method: 'POST'
      });
      
      if (response.ok) {
        showToast('Iniciando servidor de audiobook...');
        // Esperar un poco y verificar
        setTimeout(checkServerStatus, 2000);
        return;
      }
    } catch (e) {
      console.log('[Audiobook] No se pudo iniciar via servidor principal:', e);
    }
    
    // Mostrar instrucciones manuales
    showToast('Ejecuta manualmente: python start_server.py en C:\\NEVEN\\Audiobook');
    text.textContent = 'Ejecutar servidor manualmente';
    startBtn.disabled = false;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // SELECCIÓN DE ARCHIVO
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Maneja la selección de archivo PDF/EPUB
   */
  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'epub'].includes(ext)) {
      showToast('Solo se aceptan archivos PDF y EPUB');
      return;
    }
    
    state.selectedFile = file;
    
    const filenameSpan = document.getElementById('audiobook-filename');
    filenameSpan.textContent = file.name + ' (' + formatSize(file.size) + ')';
    filenameSpan.title = file.name;
    
    const convertBtn = document.getElementById('btn-audiobook-convert');
    if (state.serverOnline) {
      convertBtn.disabled = false;
    }
    
    showToast('Archivo seleccionado: ' + file.name);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CONVERSIÓN
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Inicia el proceso de conversión a audiolibro
   */
  async function startConversion() {
    if (!state.selectedFile || !state.serverOnline) {
      showToast('Selecciona un archivo y verifica que el servidor esté activo');
      return;
    }
    
    const convertBtn = document.getElementById('btn-audiobook-convert');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    const progressCard = document.getElementById('audiobook-progress-card');
    const resultCard = document.getElementById('audiobook-result-card');
    
    // Recoger configuración
    const voice = document.getElementById('audiobook-voice').value;
    const speed = document.getElementById('audiobook-speed').value;
    const translate = document.getElementById('audiobook-translate').checked;
    const saveMd = document.getElementById('audiobook-save-md').checked;
    const excludePages = document.getElementById('audiobook-exclude-pages').value;
    
    // Preparar FormData
    const formData = new FormData();
    formData.append('file', state.selectedFile);
    formData.append('voice', voice);
    formData.append('speed', speed);
    formData.append('translate', translate.toString());
    formData.append('save_markdown', saveMd.toString());
    if (excludePages) {
      formData.append('exclude_pages', excludePages);
    }
    
    // UI: mostrar progreso
    state.conversionInProgress = true;
    convertBtn.disabled = true;
    convertBtn.innerHTML = '<span class="spinner"></span> Convirtiendo...';
    cancelBtn.style.display = 'inline-block';
    progressCard.style.display = 'block';
    resultCard.style.display = 'none';
    
    updateProgress(0, 'Subiendo archivo...');
    
    try {
      // 1. Subir archivo
      const uploadResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (!uploadResponse.ok) {
        const error = await uploadResponse.json();
        throw new Error(error.error || 'Error al subir archivo');
      }
      
      const uploadData = await uploadResponse.json();
      updateProgress(10, 'Archivo subido. Iniciando conversión...');
      
      // 2. Iniciar conversión
      const convertResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: uploadData.path,  // El API espera file_path, no file_id
          voice_id: voice,
          speech_rate: parseInt(speed),
          translate: translate,
          save_markdown: saveMd,
          exclude_pages: excludePages || null
        })
      });
      
      if (!convertResponse.ok) {
        const error = await convertResponse.json();
        throw new Error(error.error || 'Error al iniciar conversión');
      }
      
      const convertData = await convertResponse.json();
      const jobId = convertData.job_id;
      
      // 3. Polling de progreso
      startProgressPolling(jobId);
      
    } catch (error) {
      console.error('[Audiobook] Error en conversión:', error);
      showToast('Error: ' + error.message);
      resetConversionUI();
    }
  }

  /**
   * Polling del progreso de conversión
   */
  function startProgressPolling(jobId) {
    if (state.pollInterval) {
      clearInterval(state.pollInterval);
    }
    
    state.pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${AUDIOBOOK_API_BASE}/api/job/${jobId}`);
        if (!response.ok) {
          throw new Error('Error al obtener estado');
        }
        
        const data = await response.json();
        
        if (data.status === 'running' || data.status === 'pending') {
          updateProgress(data.progress || 0, data.stage || 'Procesando...');
          if (data.detail) {
            document.getElementById('audiobook-progress-detail').textContent = data.detail;
          }
        } else if (data.status === 'completed') {
          clearInterval(state.pollInterval);
          state.pollInterval = null;
          updateProgress(100, '¡Completado!');
          // El resultado está en data.result
          showResult(data.result || data);
        } else if (data.status === 'failed') {
          clearInterval(state.pollInterval);
          state.pollInterval = null;
          throw new Error(data.error || 'La conversión falló');
        }
        
      } catch (error) {
        console.error('[Audiobook] Error en polling:', error);
        clearInterval(state.pollInterval);
        state.pollInterval = null;
        showToast('Error: ' + error.message);
        resetConversionUI();
      }
    }, 2000); // Polling cada 2 segundos
  }

  /**
   * Actualiza la barra de progreso
   */
  function updateProgress(percent, stage) {
    const bar = document.getElementById('audiobook-progress-bar');
    const stageSpan = document.getElementById('audiobook-progress-stage');
    const percentSpan = document.getElementById('audiobook-progress-percent');
    
    bar.style.width = percent + '%';
    stageSpan.textContent = stage;
    percentSpan.textContent = Math.round(percent) + '%';
  }

  /**
   * Muestra el resultado de la conversión
   */
  function showResult(result) {
    state.lastResult = result;
    state.conversionInProgress = false;
    
    const progressCard = document.getElementById('audiobook-progress-card');
    const resultCard = document.getElementById('audiobook-result-card');
    
    progressCard.style.display = 'none';
    resultCard.style.display = 'block';
    
    // Llenar datos
    document.getElementById('audiobook-result-title').textContent = result.title || 'Audiolibro';
    document.getElementById('audiobook-result-author').textContent = result.author || 'Autor desconocido';
    document.getElementById('audiobook-result-chapters').textContent = 
      (result.chapters || 0) + ' capítulos';
    document.getElementById('audiobook-result-duration').textContent = 
      'Duración: ' + formatDuration(result.duration_seconds || result.duration);
    
    // Construir URL de descarga
    if (result.output_path) {
      const filename = result.output_path.split(/[/\\]/).pop();
      state.lastResult.filename = filename;
      state.lastResult.download_url = `${AUDIOBOOK_API_BASE}/api/download/${encodeURIComponent(filename)}`;
    }
    
    // Portada (si existe)
    const coverImg = document.getElementById('audiobook-cover');
    if (result.cover_url) {
      coverImg.src = result.cover_url;
      coverImg.style.display = 'block';
    } else {
      coverImg.src = '';
      coverImg.style.background = '#333';
    }
    
    resetConversionUI();
    showToast('¡Audiolibro generado exitosamente!');
  }

  /**
   * Resetea la UI de conversión
   */
  function resetConversionUI() {
    const convertBtn = document.getElementById('btn-audiobook-convert');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    
    state.conversionInProgress = false;
    convertBtn.disabled = !state.selectedFile || !state.serverOnline;
    convertBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5,3 19,12 5,21"/></svg>
      Convertir a Audiolibro
    `;
    cancelBtn.style.display = 'none';
  }

  /**
   * Cancela la conversión en progreso
   */
  async function cancelConversion() {
    if (state.pollInterval) {
      clearInterval(state.pollInterval);
      state.pollInterval = null;
    }
    
    // TODO: Enviar señal de cancelación al servidor
    
    showToast('Conversión cancelada');
    resetConversionUI();
    document.getElementById('audiobook-progress-card').style.display = 'none';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DESCARGA Y QR
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Descarga el archivo M4B generado
   */
  function downloadResult() {
    if (!state.lastResult || !state.lastResult.download_url) {
      showToast('No hay archivo para descargar');
      return;
    }
    
    const a = document.createElement('a');
    a.href = state.lastResult.download_url;
    a.download = state.lastResult.filename || 'audiolibro.m4b';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }

  /**
   * Muestra el código QR para transferir al móvil
   */
  async function showQR() {
    if (!state.lastResult) {
      showToast('No hay audiolibro para transferir');
      return;
    }
    
    const modal = document.getElementById('audiobook-qr-modal');
    const qrContainer = document.getElementById('audiobook-qr-code');
    
    // Limpiar QR anterior
    qrContainer.innerHTML = '<span style="color:#888">Generando QR...</span>';
    modal.style.display = 'flex';  // Cambiar a flex para centrar contenido
    
    try {
      // Primero preparar el archivo para servir
      await fetch(`${AUDIOBOOK_API_BASE}/api/serve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: state.lastResult.filename
        })
      });
      
      // Obtener la imagen QR del servidor
      const qrUrl = `${AUDIOBOOK_API_BASE}/api/qr`;
      qrContainer.innerHTML = `<img src="${qrUrl}" alt="QR Code" style="width:200px;height:200px">`;
      
    } catch (error) {
      console.error('[Audiobook] Error generando QR:', error);
      qrContainer.innerHTML = '<span style="color:#e74c3c">Error al generar QR</span>';
    }
  }

  /**
   * Prepara para una nueva conversión
   */
  function newConversion() {
    state.selectedFile = null;
    state.lastResult = null;
    
    // Limpiar UI
    document.getElementById('audiobook-filename').textContent = '';
    document.getElementById('audiobook-file-picker').value = '';
    document.getElementById('audiobook-progress-card').style.display = 'none';
    document.getElementById('audiobook-result-card').style.display = 'none';
    document.getElementById('btn-audiobook-convert').disabled = true;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // INICIALIZACIÓN
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Inicializa el módulo de Audiobook
   */
  function init() {
    console.log('[Audiobook] Inicializando módulo...');
    
    // Event listeners
    const fileSelect = document.getElementById('btn-audiobook-select');
    const filePicker = document.getElementById('audiobook-file-picker');
    const convertBtn = document.getElementById('btn-audiobook-convert');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    const startServerBtn = document.getElementById('btn-audiobook-start-server');
    const downloadBtn = document.getElementById('btn-audiobook-download');
    const qrBtn = document.getElementById('btn-audiobook-qr');
    const newBtn = document.getElementById('btn-audiobook-new');
    const speedSlider = document.getElementById('audiobook-speed');
    const speedValue = document.getElementById('audiobook-speed-value');
    
    if (fileSelect && filePicker) {
      fileSelect.addEventListener('click', () => filePicker.click());
      filePicker.addEventListener('change', handleFileSelect);
    }
    
    if (convertBtn) {
      convertBtn.addEventListener('click', startConversion);
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', cancelConversion);
    }
    
    if (startServerBtn) {
      startServerBtn.addEventListener('click', startServer);
    }
    
    if (downloadBtn) {
      downloadBtn.addEventListener('click', downloadResult);
    }
    
    if (qrBtn) {
      qrBtn.addEventListener('click', showQR);
    }
    
    if (newBtn) {
      newBtn.addEventListener('click', newConversion);
    }
    
    if (speedSlider && speedValue) {
      speedSlider.addEventListener('input', function() {
        const val = parseInt(this.value);
        speedValue.textContent = (val >= 0 ? '+' : '') + val + '%';
      });
    }
    
    // Cerrar modal QR al hacer clic fuera
    const qrModal = document.getElementById('audiobook-qr-modal');
    if (qrModal) {
      qrModal.addEventListener('click', function(e) {
        if (e.target === qrModal) {
          qrModal.style.display = 'none';
        }
      });
    }
    
    // Verificar estado del servidor al inicio y cada 30 segundos
    checkServerStatus();
    setInterval(checkServerStatus, 30000);
    
    console.log('[Audiobook] Módulo inicializado');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EXPORTAR API PÚBLICA
  // ═══════════════════════════════════════════════════════════════════════════

  window.NEVENAudiobook = {
    init: init,
    checkServerStatus: checkServerStatus,
    startConversion: startConversion,
    cancelConversion: cancelConversion,
    showQR: showQR,
    getState: () => ({ ...state })
  };

  // Auto-inicializar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // DOM ya cargado (script cargado con defer o al final del body)
    init();
  }

})();
