# Impress.js Presentation Editor - VERSIÓN ESTABLE

## 🚀 Editor de Presentaciones Profesional

Esta es la **versión estable** del editor de presentaciones basado en Impress.js, lista para uso en producción con todas las funcionalidades avanzadas implementadas.

## ✨ Características Principales

### 🎯 Editor Completo
- **Interfaz de tres paneles**: Lista de slides, canvas visual, panel de propiedades
- **Drag-and-drop**: Arrastra slides en el canvas para posicionarlos
- **Edición en tiempo real**: Cambios instantáneos en propiedades
- **Historial completo**: Undo/Redo ilimitado

### 📊 Tipos de Slides
- **Texto**: Slides normales con formato markdown
- **Título**: Slides de título con escalado automático
- **Imagen**: Integración de imágenes desde URL
- **Sitio Web**: Embed de páginas web con iframe
- **Gráfico**: Visualización de datos desde Excel
- **Pizarra**: Canvas interactivo para dibujar
- **Vista General**: Slide de overview automático

### 📈 Sistema de Gráficos
- **Importación Excel**: Carga archivos .xlsx directamente
- **6 Paletas de colores**: Esquemas predefinidos profesionales
- **Tipos múltiples**: Líneas, barras, circular, puntos
- **Configuración avanzada**: Selección de hojas, columnas y tipos
- **Interactividad completa**: Gráficos funcionales en exportación

### 🎨 Pizarra Interactiva
- **5 Colores de tiza**: Blanco, amarillo, rosa, azul, verde
- **Herramientas**: Tiza, borrador, limpiar
- **Grosor variable**: 2-20px ajustable
- **Scroll vertical**: Canvas expandido para contenido largo
- **Atajos de teclado**: 1-5 colores, +/- grosor, flechas scroll

### 🔄 Carga de Presentaciones
- **Importación HTML**: Carga presentaciones existentes
- **Detección automática**: Reconoce tipos de slides
- **Edición completa**: Modifica presentaciones importadas
- **Compatibilidad**: Funciona con exportaciones previas

## 🚀 Inicio Rápido

### 1. Abrir el Editor
```bash
# Simplemente abre index.html en tu navegador
open index.html
```

### 2. Crear tu Primera Presentación
1. **Agregar slides**: Botón "Slide" en la toolbar
2. **Editar contenido**: Panel de propiedades a la derecha
3. **Posicionar**: Arrastra slides en el canvas central
4. **Vista previa**: Botón "Preview" para ver animaciones
5. **Exportar**: Botón "Export" para generar HTML

### 3. Trabajar con Gráficos
1. **Crear slide de gráfico**: Selecciona tipo "Gráfico"
2. **Subir Excel**: Botón "Archivo Excel (.xlsx)"
3. **Configurar datos**: Selecciona hoja, columnas y tipo
4. **Generar**: El gráfico aparece automáticamente

### 4. Usar la Pizarra
1. **Crear slide de pizarra**: Selecciona tipo "Pizarra"
2. **Se abre automáticamente**: Modal de pizarra interactiva
3. **Dibujar**: Selecciona color y grosor, dibuja con el mouse
4. **Guardar**: Botón "Guardar Pizarra"

## 🎨 Personalización

### Colores y Tipografía
- **Color de texto por defecto**: rgb(64, 73, 79)
- **Esquema de colores**: Verde (#c2d395) y grises
- **Fuentes disponibles**: Arial, Times, Courier, Helvetica, Georgia, Verdana, Comic Sans, Impact

### Posicionamiento 3D
- **Coordenadas X, Y, Z**: Posicionamiento libre en espacio 3D
- **Rotación**: 0-360 grados
- **Escala**: 0.1x a 10x
- **Canvas visual**: Representación en tiempo real

### Transparencia Visual
- **95% transparencia**: Slides inactivos se atenúan
- **Exclusión de media**: Gráficos e iframes mantienen opacidad
- **Mejor enfoque**: Solo el slide activo es completamente visible

## 📤 Exportación

### Características del HTML Exportado
- **Standalone completo**: No requiere archivos adicionales
- **CDN integrados**: Impress.js 1.1.0 y Chart.js
- **Contador de slides**: Posición actual visible
- **Animaciones funcionales**: Todas las transiciones de Impress.js
- **Gráficos interactivos**: Hover y click events funcionales
- **Pizarra con controles**: Dibujo interactivo en presentación

### Dimensiones de Media
- **Imágenes**: 80vw x 60vh
- **Sitios web**: 90vw x 80vh
- **Gráficos**: 800px x 600px
- **Pizarra**: 85vw x 70vh

## 🔧 Tecnologías Utilizadas

- **Impress.js 1.1.0**: Motor de presentaciones 3D
- **Chart.js**: Generación de gráficos dinámicos
- **SheetJS**: Procesamiento de archivos Excel
- **Vanilla JavaScript**: Sin dependencias de frameworks
- **CSS Grid/Flexbox**: Layout moderno y responsivo
- **HTML5 APIs**: FileReader, postMessage, drag-and-drop

## 📋 Requisitos del Sistema

### Navegadores Soportados
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

### Resoluciones
- Mínimo: 1024x768
- Recomendado: 1920x1080 o superior
- Responsive: Se adapta a diferentes tamaños

## 🐛 Limitaciones Conocidas

1. **Dependencias CDN**: Requiere conexión a internet para CDNs
2. **Navegación iframe**: Sitios web son solo visualización en exportación
3. **Formato Excel**: Solo .xlsx soportado
4. **Navegadores antiguos**: Requiere soporte CSS3 transforms

## 📞 Soporte

### Archivos de Documentación
- `PROMPT.md`: Documentación técnica completa
- `VERSION.md`: Información de versión y changelog
- `README.md`: Esta guía de usuario

### Estructura de Archivos
```
ESTABLE/
├── index.html          # Interfaz principal
├── script.js           # Lógica JavaScript
├── styles.css          # Estilos CSS
├── preview.html        # Vista previa
├── PROMPT.md          # Documentación técnica
├── VERSION.md         # Información de versión
└── README.md          # Guía de usuario
```

## 🎯 Estado del Proyecto

**VERSIÓN ESTABLE 2.0.0** - Lista para producción

✅ Todas las funcionalidades implementadas  
✅ Exportación completamente funcional  
✅ Gráficos interactivos  
✅ Pizarra funcional  
✅ Carga de presentaciones  
✅ Interfaz pulida y profesional  
✅ Documentación completa  

---

**¡Disfruta creando presentaciones increíbles con Impress.js!** 🎉