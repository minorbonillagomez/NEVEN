/**
 * NEVEN Studio - Audiobook Tab Handler (v2.0)
 * Pipeline de 2 pasos: PDF/EPUB -> Markdown -> M4B
 * 
 * Paso 1: Extraer documento a Markdown (para revision humana)
 * Paso 2: Generar audiolibro M4B desde Markdown revisado
 * 
 * Puerto del servidor: 5556 (separado del servidor principal en 5555)
 * @version 2.0.0
 * @date 2026-08-19
 */

(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFIGURACION
  // ═══════════════════════════════════════════════════════════════════════════
  
  const AUDIOBOOK_PORT = 5556;
  const AUDIOBOOK_API_BASE = `http://localhost:${AUDIOBOOK_PORT}`;
  
  // Estado global del modulo
  const state = {
    serverOnline: false,
    // Paso 1
    selectedPdfFile: null,
    extractedMdPath: null,
    extractedMdFilename: null,
    // Paso 2
    selectedMdFile: null,
    selectedMdContent: null,
    // General
    conversionInProgress: false,
    lastResult: null,
    pollInterval: null
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // UTILIDADES
  // ═══════════════════════════════════════════════════════════════════════════

  function showToast(message, duration = 3000) {
    if (typeof window.showToast === 'function') {
      window.showToast(message, duration);
    } else {
      console.log('[Audiobook]', message);
    }
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return 'N/A';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m`;
    return `${m}m ${s}s`;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // VERIFICACION DEL SERVIDOR
  // ═══════════════════════════════════════════════════════════════════════════

  async function checkServerStatus() {
    const dot = document.getElementById('audiobook-server-dot');
    const text = document.getElementById('audiobook-server-text');
    const startBtn = document.getElementById('btn-audiobook-start-server');

    try {
      const response = await fetch(`${AUDIOBOOK_API_BASE}/api/health`, {
        method: 'GET',
        mode: 'cors'
      });
      
      if (response.ok) {
        const data = await response.json();
        state.serverOnline = true;
        
        dot.style.background = '#27ae60';
        text.textContent = `Servidor activo v${data.version || '1.0.0'}`;
        text.style.color = '#27ae60';
        startBtn.style.display = 'none';
        
        updateButtonStates();
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
    
    updateButtonStates();
    return false;
  }

  async function startServer() {
    const startBtn = document.getElementById('btn-audiobook-start-server');
    const text = document.getElementById('audiobook-server-text');
    
    startBtn.disabled = true;
    text.textContent = 'Iniciando servidor...';
    
    try {
      const response = await fetch('http://localhost:5555/api/audiobook/start', {
        method: 'POST'
      });
      
      if (response.ok) {
        showToast('Iniciando servidor de audiobook...');
        setTimeout(checkServerStatus, 2000);
        return;
      }
    } catch (e) {
      console.log('[Audiobook] No se pudo iniciar via servidor principal');
    }
    
    showToast('Ejecuta: python neven_audiobook_server.py en C:\\NEVEN\\Audiobook');
    text.textContent = 'Ejecutar servidor manualmente';
    startBtn.disabled = false;
  }

  function updateButtonStates() {
    const extractBtn = document.getElementById('btn-audiobook-extract');
    const generateBtn = document.getElementById('btn-audiobook-generate');
    
    if (extractBtn) {
      extractBtn.disabled = !state.serverOnline || !state.selectedPdfFile;
    }
    
    if (generateBtn) {
      generateBtn.disabled = !state.serverOnline || (!state.selectedMdFile && !state.extractedMdPath);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PREVIEW DE VOZ (muestra de 5 segundos)
  // ═══════════════════════════════════════════════════════════════════════════

  async function previewVoice() {
    if (!state.serverOnline) {
      showToast('El servidor no esta disponible');
      return;
    }

    const voiceSelect = document.getElementById('audiobook-voice');
    const previewBtn = document.getElementById('btn-audiobook-preview-voice');
    const previewText = document.getElementById('audiobook-preview-text');
    const audioEl = document.getElementById('audiobook-voice-preview');
    
    if (!voiceSelect || !previewBtn || !audioEl) return;

    const voice = voiceSelect.value;
    const speed = parseInt(document.getElementById('audiobook-speed')?.value || '0');
    
    // Determinar texto de muestra segun idioma
    let sampleText;
    if (voice.startsWith('es-')) {
      sampleText = 'Hola, esta es una muestra de mi voz. Asi sonara tu audiolibro cuando lo generes con NEVEN Studio.';
    } else if (voice.startsWith('en-')) {
      sampleText = 'Hello, this is a sample of my voice. This is how your audiobook will sound when you generate it with NEVEN Studio.';
    } else {
      sampleText = 'Esta es una muestra de la voz seleccionada para tu audiolibro.';
    }

    // UI: mostrar cargando
    previewBtn.disabled = true;
    previewText.textContent = 'Cargando...';

    try {
      const response = await fetch(`${AUDIOBOOK_API_BASE}/api/preview-voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          voice: voice,
          text: sampleText,
          speed: speed
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Obtener el audio como blob
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Reproducir
      audioEl.src = audioUrl;
      audioEl.onended = () => {
        previewText.textContent = 'Probar';
        previewBtn.disabled = false;
        URL.revokeObjectURL(audioUrl);
      };
      audioEl.onerror = () => {
        previewText.textContent = 'Probar';
        previewBtn.disabled = false;
        showToast('Error al reproducir audio');
      };
      
      previewText.textContent = 'Reproduciendo...';
      await audioEl.play();

    } catch (e) {
      console.error('[Audiobook] Error en preview:', e);
      showToast('Error al generar muestra de voz');
      previewText.textContent = 'Probar';
      previewBtn.disabled = false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PASO 1: EXTRACCION PDF/EPUB -> MARKDOWN
  // ═══════════════════════════════════════════════════════════════════════════

  function handlePdfFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'epub'].includes(ext)) {
      showToast('Solo se aceptan archivos PDF y EPUB');
      return;
    }
    
    state.selectedPdfFile = file;
    
    const filenameSpan = document.getElementById('audiobook-pdf-filename');
    filenameSpan.textContent = file.name + ' (' + formatSize(file.size) + ')';
    
    updateButtonStates();
    showToast('Archivo seleccionado: ' + file.name);
  }

  async function extractToMarkdown() {
    if (!state.selectedPdfFile || !state.serverOnline) {
      showToast('Selecciona un archivo y verifica el servidor');
      return;
    }
    
    const extractBtn = document.getElementById('btn-audiobook-extract');
    const progressCard = document.getElementById('audiobook-progress-card');
    const progressTitle = document.getElementById('audiobook-progress-title');
    const mdResultCard = document.getElementById('audiobook-md-result-card');
    
    // UI: mostrar progreso
    extractBtn.disabled = true;
    extractBtn.innerHTML = '<span class="spinner"></span> Extrayendo...';
    progressCard.style.display = 'block';
    progressTitle.textContent = 'Extrayendo texto...';
    mdResultCard.style.display = 'none';
    
    updateProgress(0, 'Subiendo archivo...');
    
    try {
      // 1. Subir archivo
      const formData = new FormData();
      formData.append('file', state.selectedPdfFile);
      
      const uploadResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });
      
      if (!uploadResponse.ok) {
        const error = await uploadResponse.json();
        throw new Error(error.error || 'Error al subir archivo');
      }
      
      const uploadData = await uploadResponse.json();
      updateProgress(30, 'Archivo subido. Extrayendo texto...');
      
      // 2. Extraer a Markdown
      const startPage = parseInt(document.getElementById('audiobook-start-page').value) || 1;
      const excludePages = document.getElementById('audiobook-exclude-pages').value;
      
      const extractResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: uploadData.path,
          start_page: startPage,
          exclude_pages: excludePages || null
        })
      });
      
      if (!extractResponse.ok) {
        const error = await extractResponse.json();
        throw new Error(error.error || 'Error al extraer texto');
      }
      
      const extractData = await extractResponse.json();
      updateProgress(100, 'Extraccion completada');
      
      // Guardar resultado
      state.extractedMdPath = extractData.markdown_path;
      state.extractedMdFilename = extractData.markdown_filename;
      
      // Mostrar resultado
      document.getElementById('audiobook-md-filename').textContent = extractData.markdown_filename;
      document.getElementById('audiobook-md-stats').textContent = 
        `${extractData.chapters || 0} capitulos | ${extractData.words || 0} palabras | ~${extractData.estimated_hours || 0}h de audio`;
      
      progressCard.style.display = 'none';
      mdResultCard.style.display = 'block';
      
      showToast('Markdown extraido correctamente');
      
    } catch (error) {
      console.error('[Audiobook] Error en extraccion:', error);
      showToast('Error: ' + error.message);
      progressCard.style.display = 'none';
    } finally {
      extractBtn.disabled = false;
      extractBtn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        Extraer Markdown
      `;
      updateButtonStates();
    }
  }

  async function downloadMarkdown() {
    if (!state.extractedMdFilename) {
      showToast('No hay Markdown para descargar');
      return;
    }
    
    try {
      const response = await fetch(`${AUDIOBOOK_API_BASE}/api/markdown/${encodeURIComponent(state.extractedMdFilename)}`);
      if (!response.ok) throw new Error('Error al obtener archivo');
      
      const data = await response.json();
      
      // Crear blob y descargar
      const blob = new Blob([data.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = state.extractedMdFilename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showToast('Descargando ' + state.extractedMdFilename);
    } catch (error) {
      showToast('Error al descargar: ' + error.message);
    }
  }

  async function previewMarkdown() {
    if (!state.extractedMdFilename) {
      showToast('No hay Markdown para previsualizar');
      return;
    }
    
    const modal = document.getElementById('audiobook-preview-modal');
    const content = document.getElementById('audiobook-preview-content');
    
    content.textContent = 'Cargando...';
    modal.style.display = 'block';
    
    try {
      const response = await fetch(`${AUDIOBOOK_API_BASE}/api/markdown/${encodeURIComponent(state.extractedMdFilename)}`);
      if (!response.ok) throw new Error('Error al obtener archivo');
      
      const data = await response.json();
      content.textContent = data.content;
    } catch (error) {
      content.textContent = 'Error al cargar: ' + error.message;
    }
  }

  function useMarkdownDirectly() {
    if (!state.extractedMdPath) {
      showToast('Primero extrae un documento');
      return;
    }
    
    // Marcar que usaremos el MD extraido directamente
    state.selectedMdFile = null; // No hay archivo local
    state.selectedMdContent = null;
    
    document.getElementById('audiobook-md-selected').textContent = 
      state.extractedMdFilename + ' (del Paso 1)';
    
    updateButtonStates();
    showToast('Usando Markdown del Paso 1');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PASO 2: MARKDOWN -> M4B
  // ═══════════════════════════════════════════════════════════════════════════

  function handleMdFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['md', 'txt'].includes(ext)) {
      showToast('Solo se aceptan archivos .md o .txt');
      return;
    }
    
    state.selectedMdFile = file;
    state.extractedMdPath = null; // Ya no usamos el extraido
    
    document.getElementById('audiobook-md-selected').textContent = 
      file.name + ' (' + formatSize(file.size) + ')';
    
    updateButtonStates();
    showToast('Markdown cargado: ' + file.name);
  }

  async function generateAudiobook() {
    if (!state.serverOnline) {
      showToast('El servidor no esta disponible');
      return;
    }
    
    if (!state.selectedMdFile && !state.extractedMdPath) {
      showToast('Carga un archivo Markdown o usa el del Paso 1');
      return;
    }
    
    const generateBtn = document.getElementById('btn-audiobook-generate');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    const progressCard = document.getElementById('audiobook-progress-card');
    const progressTitle = document.getElementById('audiobook-progress-title');
    const resultCard = document.getElementById('audiobook-result-card');
    
    // Recoger configuracion
    const voice = document.getElementById('audiobook-voice').value;
    const speed = parseInt(document.getElementById('audiobook-speed').value);
    const translate = document.getElementById('audiobook-translate').checked;
    const offline = document.getElementById('audiobook-offline').checked;
    
    // UI
    state.conversionInProgress = true;
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner"></span> Generando...';
    cancelBtn.style.display = 'inline-block';
    progressCard.style.display = 'block';
    progressTitle.textContent = 'Generando audiolibro...';
    resultCard.style.display = 'none';
    
    updateProgress(0, 'Preparando...');
    
    try {
      let mdFilename = state.extractedMdFilename;
      
      // Si hay archivo local seleccionado, subirlo primero
      if (state.selectedMdFile) {
        updateProgress(5, 'Subiendo Markdown...');
        
        const formData = new FormData();
        formData.append('file', state.selectedMdFile);
        
        const uploadResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/markdown/upload`, {
          method: 'POST',
          body: formData
        });
        
        if (!uploadResponse.ok) {
          const error = await uploadResponse.json();
          throw new Error(error.error || 'Error al subir Markdown');
        }
        
        const uploadData = await uploadResponse.json();
        mdFilename = uploadData.filename;
      }
      
      updateProgress(10, 'Iniciando generacion de audio...');
      
      // Llamar a generar desde Markdown
      const generateResponse = await fetch(`${AUDIOBOOK_API_BASE}/api/generate-from-markdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          markdown_filename: mdFilename,
          voice_id: voice,
          speech_rate: speed,
          translate: translate,
          offline: offline
        })
      });
      
      if (!generateResponse.ok) {
        const error = await generateResponse.json();
        throw new Error(error.error || 'Error al iniciar generacion');
      }
      
      const generateData = await generateResponse.json();
      const jobId = generateData.job_id;
      
      // Polling de progreso
      startProgressPolling(jobId);
      
    } catch (error) {
      console.error('[Audiobook] Error en generacion:', error);
      showToast('Error: ' + error.message);
      resetGenerationUI();
    }
  }

  function startProgressPolling(jobId) {
    if (state.pollInterval) {
      clearInterval(state.pollInterval);
    }
    
    state.pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${AUDIOBOOK_API_BASE}/api/job/${jobId}`);
        if (!response.ok) throw new Error('Error al obtener estado');
        
        const data = await response.json();
        
        if (data.status === 'running' || data.status === 'pending') {
          updateProgress(data.progress || 0, data.stage || 'Procesando...');
          if (data.detail) {
            document.getElementById('audiobook-progress-detail').textContent = data.detail;
          }
        } else if (data.status === 'completed') {
          clearInterval(state.pollInterval);
          state.pollInterval = null;
          updateProgress(100, 'Completado!');
          showResult(data.result || data);
        } else if (data.status === 'failed') {
          clearInterval(state.pollInterval);
          state.pollInterval = null;
          throw new Error(data.error || 'La generacion fallo');
        }
        
      } catch (error) {
        console.error('[Audiobook] Error en polling:', error);
        clearInterval(state.pollInterval);
        state.pollInterval = null;
        showToast('Error: ' + error.message);
        resetGenerationUI();
      }
    }, 2000);
  }

  function updateProgress(percent, stage) {
    const bar = document.getElementById('audiobook-progress-bar');
    const stageSpan = document.getElementById('audiobook-progress-stage');
    const percentSpan = document.getElementById('audiobook-progress-percent');
    
    bar.style.width = percent + '%';
    stageSpan.textContent = stage;
    percentSpan.textContent = Math.round(percent) + '%';
  }

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
      (result.chapters || 0) + ' capitulos';
    document.getElementById('audiobook-result-duration').textContent = 
      'Duracion: ' + formatDuration(result.duration_seconds || result.duration);
    
    // Construir URL de descarga
    if (result.output_path) {
      const filename = result.output_path.split(/[/\\]/).pop();
      state.lastResult.filename = filename;
      state.lastResult.download_url = `${AUDIOBOOK_API_BASE}/api/download/${encodeURIComponent(filename)}`;
    }
    
    // Portada
    const coverImg = document.getElementById('audiobook-cover');
    if (result.cover_url) {
      coverImg.src = result.cover_url;
    } else {
      coverImg.src = '';
      coverImg.style.background = '#333';
    }
    
    resetGenerationUI();
    showToast('Audiolibro generado exitosamente!');
  }

  function resetGenerationUI() {
    const generateBtn = document.getElementById('btn-audiobook-generate');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    
    state.conversionInProgress = false;
    generateBtn.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5,3 19,12 5,21"/></svg>
      Generar Audiolibro
    `;
    cancelBtn.style.display = 'none';
    updateButtonStates();
  }

  async function cancelGeneration() {
    if (state.pollInterval) {
      clearInterval(state.pollInterval);
      state.pollInterval = null;
    }
    
    showToast('Generacion cancelada');
    resetGenerationUI();
    document.getElementById('audiobook-progress-card').style.display = 'none';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DESCARGA Y QR
  // ═══════════════════════════════════════════════════════════════════════════

  function downloadM4B() {
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

  async function showQR() {
    if (!state.lastResult) {
      showToast('No hay audiolibro para transferir');
      return;
    }
    
    const modal = document.getElementById('audiobook-qr-modal');
    const qrContainer = document.getElementById('audiobook-qr-code');
    
    qrContainer.innerHTML = '<span style="color:#888">Generando QR...</span>';
    modal.style.display = 'flex';
    
    try {
      // Preparar archivo para servir
      await fetch(`${AUDIOBOOK_API_BASE}/api/serve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: state.lastResult.filename
        })
      });
      
      // Obtener imagen QR
      const qrUrl = `${AUDIOBOOK_API_BASE}/api/qr`;
      qrContainer.innerHTML = `<img src="${qrUrl}" alt="QR Code" style="width:200px;height:200px">`;
      
    } catch (error) {
      console.error('[Audiobook] Error generando QR:', error);
      qrContainer.innerHTML = '<span style="color:#e74c3c">Error al generar QR</span>';
    }
  }

  function newAudiobook() {
    // Resetear estado
    state.selectedPdfFile = null;
    state.extractedMdPath = null;
    state.extractedMdFilename = null;
    state.selectedMdFile = null;
    state.selectedMdContent = null;
    state.lastResult = null;
    
    // Limpiar UI
    document.getElementById('audiobook-pdf-filename').textContent = '';
    document.getElementById('audiobook-file-picker-pdf').value = '';
    document.getElementById('audiobook-md-selected').textContent = '';
    document.getElementById('audiobook-file-picker-md').value = '';
    document.getElementById('audiobook-md-result-card').style.display = 'none';
    document.getElementById('audiobook-progress-card').style.display = 'none';
    document.getElementById('audiobook-result-card').style.display = 'none';
    
    updateButtonStates();
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // INICIALIZACION
  // ═══════════════════════════════════════════════════════════════════════════

  function init() {
    console.log('[Audiobook] Inicializando modulo v2.0 (2 pasos)...');
    
    // Paso 1: Seleccion PDF/EPUB
    const pdfSelectBtn = document.getElementById('btn-audiobook-select-pdf');
    const pdfPicker = document.getElementById('audiobook-file-picker-pdf');
    const extractBtn = document.getElementById('btn-audiobook-extract');
    const downloadMdBtn = document.getElementById('btn-audiobook-download-md');
    const previewMdBtn = document.getElementById('btn-audiobook-preview-md');
    const useDirectBtn = document.getElementById('btn-audiobook-use-directly');
    
    if (pdfSelectBtn && pdfPicker) {
      pdfSelectBtn.addEventListener('click', () => pdfPicker.click());
      pdfPicker.addEventListener('change', handlePdfFileSelect);
    }
    
    if (extractBtn) {
      extractBtn.addEventListener('click', extractToMarkdown);
    }
    
    if (downloadMdBtn) {
      downloadMdBtn.addEventListener('click', downloadMarkdown);
    }
    
    if (previewMdBtn) {
      previewMdBtn.addEventListener('click', previewMarkdown);
    }
    
    if (useDirectBtn) {
      useDirectBtn.addEventListener('click', useMarkdownDirectly);
    }
    
    // Paso 2: Seleccion MD y generacion
    const mdSelectBtn = document.getElementById('btn-audiobook-select-md');
    const mdPicker = document.getElementById('audiobook-file-picker-md');
    const generateBtn = document.getElementById('btn-audiobook-generate');
    const cancelBtn = document.getElementById('btn-audiobook-cancel');
    
    if (mdSelectBtn && mdPicker) {
      mdSelectBtn.addEventListener('click', () => mdPicker.click());
      mdPicker.addEventListener('change', handleMdFileSelect);
    }
    
    if (generateBtn) {
      generateBtn.addEventListener('click', generateAudiobook);
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', cancelGeneration);
    }
    
    // Resultado
    const downloadM4BBtn = document.getElementById('btn-audiobook-download-m4b');
    const qrBtn = document.getElementById('btn-audiobook-qr');
    const newBtn = document.getElementById('btn-audiobook-new');
    
    if (downloadM4BBtn) {
      downloadM4BBtn.addEventListener('click', downloadM4B);
    }
    
    if (qrBtn) {
      qrBtn.addEventListener('click', showQR);
    }
    
    if (newBtn) {
      newBtn.addEventListener('click', newAudiobook);
    }
    
    // Servidor
    const startServerBtn = document.getElementById('btn-audiobook-start-server');
    if (startServerBtn) {
      startServerBtn.addEventListener('click', startServer);
    }
    
    // Preview de voz
    const previewVoiceBtn = document.getElementById('btn-audiobook-preview-voice');
    if (previewVoiceBtn) {
      previewVoiceBtn.addEventListener('click', previewVoice);
    }
    
    // Velocidad slider
    const speedSlider = document.getElementById('audiobook-speed');
    const speedValue = document.getElementById('audiobook-speed-value');
    if (speedSlider && speedValue) {
      speedSlider.addEventListener('input', function() {
        const val = parseInt(this.value);
        speedValue.textContent = (val >= 0 ? '+' : '') + val + '%';
      });
    }
    
    // Cerrar modales
    const qrModal = document.getElementById('audiobook-qr-modal');
    if (qrModal) {
      qrModal.addEventListener('click', function(e) {
        if (e.target === qrModal) {
          qrModal.style.display = 'none';
        }
      });
    }
    
    const previewModal = document.getElementById('audiobook-preview-modal');
    if (previewModal) {
      previewModal.addEventListener('click', function(e) {
        if (e.target === previewModal) {
          previewModal.style.display = 'none';
        }
      });
    }
    
    // Verificar servidor
    checkServerStatus();
    setInterval(checkServerStatus, 30000);
    
    console.log('[Audiobook] Modulo inicializado');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // API PUBLICA
  // ═══════════════════════════════════════════════════════════════════════════

  window.NEVENAudiobook = {
    init: init,
    checkServerStatus: checkServerStatus,
    extractToMarkdown: extractToMarkdown,
    generateAudiobook: generateAudiobook,
    cancelGeneration: cancelGeneration,
    showQR: showQR,
    getState: () => ({ ...state })
  };

  // Auto-inicializar
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
