---
id: internacionalizacion
title: "Capitulo 20 - Internacionalizacion (i18n)"
sidebar_label: 20. Internacionalizacion
sidebar_position: 20
---

# Capitulo 20: Internacionalizacion (i18n)

**Disponible desde:** Agosto 2026

NEVEN Studio soporta múltiples idiomas. Actualmente disponible en **Español** e **Inglés**, con arquitectura preparada para agregar más idiomas.

---

## 20.1 Idiomas soportados

| Código | Idioma | Estado |
|:---|:---|:---|
| `es` | Español | ✅ Completo |
| `en` | English | ✅ Completo |

---

## 20.2 Cambiar idioma

### Desde la interfaz

```
NEVEN Studio → Tab "Settings" → Sección "Idioma"
→ Seleccionar: Español | English
→ La interfaz se actualiza inmediatamente
```

### Persistencia

El idioma seleccionado se guarda en `localStorage` del navegador:
- Se mantiene entre sesiones
- Es específico por máquina/usuario
- No requiere reiniciar NEVEN

---

## 20.3 Elementos traducidos

La internacionalización cubre todos los elementos de la interfaz:

| Categoría | Elementos |
|:---|:---|
| **Navegación** | Tabs, menús, breadcrumbs |
| **Formularios** | Labels, placeholders, botones |
| **Mensajes** | Errores, confirmaciones, tooltips |
| **Data Lab** | Familias, funciones, parámetros |
| **Chart Gallery** | Filtros, acciones, descripciones |
| **Settings** | Todas las opciones de configuración |
| **Ayuda** | Documentación integrada |

### Ejemplo de traducción

| Inglés | Español |
|:---|:---|
| Run Script | Ejecutar Script |
| Load Data | Cargar Datos |
| Execute | Ejecutar |
| Save As | Guardar Como |
| Connected | Conectado |
| Disconnected | Desconectado |
| Error loading data | Error al cargar datos |

---

## 20.4 Arquitectura i18n

### Archivos de traducción

```
C:\NEVEN\TaskPane\lang\
├── es.js    ← Español (default)
├── en.js    ← English
└── (futuro: fr.js, pt.js, de.js, ...)
```

### Estructura de un archivo de idioma

```javascript
// lang/es.js
window.NEVEN_LANG = window.NEVEN_LANG || {};
window.NEVEN_LANG['es'] = {
  // Navegación
  nav: {
    dataLab: "Data Lab",
    runScript: "Ejecutar Script",
    dataStudio: "Data Studio",
    charts: "Gráficos",
    ai: "IA",
    settings: "Configuración",
    help: "Ayuda"
  },
  
  // Acciones
  actions: {
    execute: "Ejecutar",
    save: "Guardar",
    saveAs: "Guardar como",
    copy: "Copiar",
    cancel: "Cancelar",
    confirm: "Confirmar",
    delete: "Eliminar",
    edit: "Editar"
  },
  
  // Estados
  status: {
    connected: "Conectado",
    disconnected: "Desconectado",
    loading: "Cargando...",
    processing: "Procesando...",
    ready: "Listo",
    error: "Error"
  },
  
  // ... más secciones
};
```

---

## 20.5 Cómo funciona la traducción

### Atributo data-i18n

Los elementos HTML usan el atributo `data-i18n` para indicar la clave de traducción:

```html
<!-- Elemento traducible -->
<button data-i18n="actions.execute">Execute</button>

<!-- Después de aplicar i18n (español) -->
<button data-i18n="actions.execute">Ejecutar</button>
```

### Traducción de placeholders

```html
<input type="text" 
       data-i18n-placeholder="search.placeholder"
       placeholder="Search...">
```

### Traducción de tooltips

```html
<button data-i18n-title="tooltips.copyCode"
        title="Copy to clipboard">
  📋
</button>
```

---

## 20.6 Agregar un nuevo idioma

Para agregar soporte de un nuevo idioma (ej: Francés):

### Paso 1: Crear archivo de idioma

```javascript
// C:\NEVEN\TaskPane\lang\fr.js
window.NEVEN_LANG = window.NEVEN_LANG || {};
window.NEVEN_LANG['fr'] = {
  nav: {
    dataLab: "Labo de Données",
    runScript: "Exécuter Script",
    // ... todas las claves
  },
  // ... todas las secciones
};
```

### Paso 2: Agregar al selector de idiomas

En `taskpane.html`, agregar la opción al dropdown:

```html
<select id="language-selector">
  <option value="es">Español</option>
  <option value="en">English</option>
  <option value="fr">Français</option>  <!-- NUEVO -->
</select>
```

### Paso 3: Cargar el archivo

En `taskpane.html`, agregar el script:

```html
<script src="lang/es.js"></script>
<script src="lang/en.js"></script>
<script src="lang/fr.js"></script>  <!-- NUEVO -->
```

---

## 20.7 Traducción de Data Lab

Las funciones de Data Lab tienen traducciones específicas:

### Familias

| Código | Español | English |
|:---|:---|:---|
| AD | Análisis de Datos | Data Analysis |
| RG | Regresión | Regression |
| ST | Series de Tiempo | Time Series |
| DS | Conjuntos de Datos | Datasets |
| TM | Minería de Texto | Text Mining |
| UC | Mis Funciones | My Functions |

### Funciones

| Función | Español | English |
|:---|:---|:---|
| AD_ACP.C | Componentes Principales | Principal Components |
| AD_KMeans.C | K-Medias | K-Means |
| RG_Lineal.C | Regresión Lineal | Linear Regression |
| RG_Logistica.C | Regresión Logística | Logistic Regression |

### Parámetros

| Parámetro | Español | English |
|:---|:---|:---|
| n_clusters | Número de clusters | Number of clusters |
| confidence | Nivel de confianza | Confidence level |
| normalize | Normalizar datos | Normalize data |

---

## 20.8 Traducción de mensajes de error

Los mensajes de error también se traducen:

| Código | Español | English |
|:---|:---|:---|
| `ERR_NO_DATA` | No hay datos cargados | No data loaded |
| `ERR_ENGINE_OFF` | Motor no disponible | Engine not available |
| `ERR_TIMEOUT` | Tiempo de espera agotado | Request timed out |
| `ERR_PARSE` | Error al procesar respuesta | Error parsing response |
| `ERR_NETWORK` | Error de conexión | Network error |

---

## 20.9 Detección automática de idioma

NEVEN intenta detectar el idioma preferido del usuario:

```
1. Verificar localStorage (idioma guardado previamente)
2. Si no existe → verificar navigator.language del navegador
3. Si no es soportado → usar español (default)
```

### Ejemplo de detección

```javascript
function detectLanguage() {
  // 1. Idioma guardado
  const saved = localStorage.getItem('neven-language');
  if (saved && NEVEN_LANG[saved]) return saved;
  
  // 2. Idioma del navegador
  const browser = navigator.language.split('-')[0]; // "es-CR" → "es"
  if (NEVEN_LANG[browser]) return browser;
  
  // 3. Default
  return 'es';
}
```

---

## 20.10 API de internacionalización

### Obtener traducción por código

```javascript
// Función auxiliar
function t(key) {
  const lang = getCurrentLanguage();
  const keys = key.split('.');
  let value = NEVEN_LANG[lang];
  for (const k of keys) {
    value = value?.[k];
  }
  return value || key;
}

// Uso
console.log(t('actions.execute')); // "Ejecutar" o "Execute"
```

### Cambiar idioma programáticamente

```javascript
function setLanguage(langCode) {
  if (!NEVEN_LANG[langCode]) {
    console.error(`Idioma no soportado: ${langCode}`);
    return;
  }
  localStorage.setItem('neven-language', langCode);
  applyTranslations(langCode);
}
```

### Aplicar traducciones al DOM

```javascript
function applyTranslations(langCode) {
  const translations = NEVEN_LANG[langCode];
  
  // Traducir contenido de texto
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = getNestedValue(translations, key);
    if (text) el.textContent = text;
  });
  
  // Traducir placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const text = getNestedValue(translations, key);
    if (text) el.placeholder = text;
  });
  
  // Traducir títulos (tooltips)
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const text = getNestedValue(translations, key);
    if (text) el.title = text;
  });
}
```

---

## 20.11 Consideraciones para traductores

### Longitud de texto

Algunos idiomas requieren más espacio que otros:

| Español | Inglés | Alemán |
|:---|:---|:---|
| Ejecutar | Execute | Ausführen |
| Guardar como | Save As | Speichern unter |

**Recomendación:** Probar la UI después de traducir para verificar que los textos caben en los botones y menús.

### Contexto

Algunas palabras cambian según el contexto:

| Inglés | Contexto | Español |
|:---|:---|:---|
| Run | Ejecutar código | Ejecutar |
| Run | Correr/moverse | Correr |
| Save | Guardar archivo | Guardar |
| Save | Ahorrar dinero | Ahorrar |

### Plurales

NEVEN no maneja plurales complejos automáticamente. Para casos donde se necesita:

```javascript
// Enfoque simple
function pluralize(count, singular, plural) {
  return count === 1 ? singular : plural;
}

// Uso
const msg = `${count} ${pluralize(count, 'archivo', 'archivos')} procesado${count === 1 ? '' : 's'}`;
```

---

## 20.12 Troubleshooting

**El idioma no cambia:**
- Verificar que el archivo de idioma esté cargado (F12 → Network)
- Verificar que el código de idioma sea correcto ('es', 'en')
- Limpiar localStorage y recargar

**Texto sin traducir:**
- Verificar que el elemento tenga `data-i18n` correcto
- Verificar que la clave exista en el archivo de idioma
- Revisar la consola por errores de JavaScript

**Traducción incorrecta:**
- Verificar que la clave apunte al texto correcto
- Algunos textos pueden ser dinámicos (generados por JS)

---

*Documentación actualizada: Agosto 2026*

*Sistema de Internacionalización — Agosto 2026*
*Universidad de Costa Rica — Tesis de Maestría*

