# Impress.js Presentation Editor - Complete Implementation Guide

## Overview
Complete web-based presentation editor using Impress.js with drag-and-drop functionality, real-time editing, chart integration, and fully functional export capabilities.

## Core Features Implemented

### 1. Editor Interface
- **Three-panel layout**: Slides list (left), canvas (center), properties panel (right)
- **Toolbar**: Add slide, delete slide, preview, export, load presentation, undo/redo buttons
- **Modern UI**: Clean design with green accent colors (#c2d395, #abb3c6)
- **Discrete iconography**: Line-style icons with 80% opacity for visual harmony

### 2. Slide Management
- **Default example**: 15 pre-loaded slides including chart and blackboard demos
- **Add/Delete slides**: Full CRUD operations with validation (minimum 1 slide)
- **Drag-and-drop reordering**: Slides can be reordered in the left panel
- **Slide types**: Normal slide, title, image, iframe (website), chart, blackboard, overview

### 3. Canvas Functionality
- **Visual representation**: All slides displayed simultaneously on canvas
- **Drag-and-drop positioning**: Click and drag slides to reposition them
- **Real-time updates**: Canvas updates immediately when properties change
- **Visual indicators**: "SITIO WEB" for iframes, "GRÁFICO" for charts with distinct colors
- **Spatial awareness**: Shows relative positioning of all slides

### 4. Properties Panel
- **Text editing**: Textarea for slide content with markdown support (**bold**, *italic*)
- **Positioning**: X, Y, Z coordinates with numeric inputs
- **Transformation**: Rotation (0-360°) and scale (0.1-10x)
- **Typography**: Font family selector, font size (8-200px), color picker
- **Media support**: Image URL input, iframe URL input for websites
- **Chart integration**: Excel file upload with Chart.js integration

### 5. Chart System
- **Excel integration**: Upload .xlsx files for data visualization
- **Chart types**: Line, bar, pie, scatter plots
- **Color palettes**: 6 predefined color schemes (default, blue, green, warm, cool, monochrome)
- **Interactive configuration**: Sheet selection, column mapping, chart customization
- **Dynamic data**: Automatic date label generation for time series

### 6. Preview System
- **Modal preview**: Full-screen preview with working animations
- **PostMessage communication**: Iframe-based preview with message passing
- **Real-time loading**: Preview updates with current slide configuration
- **Chart rendering**: Full Chart.js functionality in preview mode

### 7. Export Functionality
- **Standalone HTML**: Generates complete presentation file with all dependencies
- **Impress.js integration**: Uses CDN version 1.1.0 for compatibility
- **Chart.js integration**: Includes Chart.js CDN for dynamic charts
- **Working animations**: All Impress.js transitions and effects functional
- **Proper sizing**: Iframes (90vw x 80vh), images (80vw x 60vh), charts (800x600px)
- **Slide counter**: 32px counter in bottom-right corner

### 8. Advanced Features
- **Undo/Redo**: Complete history management with state saving
- **Load presentations**: Import existing HTML presentations for editing
- **Blackboard functionality**: Interactive drawing canvas with multiple tools
- **Visual transparency**: 95% transparency for inactive slides (excluding media)
- **Responsive design**: Works on different screen sizes
- **Error handling**: Graceful error management and user feedback
- **Cross-browser compatibility**: Works in modern browsers
- **XLSX processing**: Client-side Excel file parsing with SheetJS

## Technical Implementation

### File Structure
```
editor/
├── index.html          # Main editor interface
├── script.js           # Core JavaScript functionality
├── styles.css          # CSS styling
├── preview.html        # Preview iframe template
└── PROMPT.md          # This documentation
```

### Key Technologies
- **Impress.js 1.1.0**: Core presentation engine
- **Chart.js**: Dynamic chart generation and rendering
- **SheetJS (XLSX)**: Excel file processing and data extraction
- **Vanilla JavaScript**: No external frameworks
- **CSS Grid/Flexbox**: Modern layout techniques
- **HTML5 APIs**: File download, drag-and-drop, postMessage, FileReader

### CSS Specifications
- **Color scheme**: Green accents (#c2d395), gray backgrounds (#abb3c6)
- **Typography**: General Sans font family
- **Layout**: Three-panel responsive design
- **Canvas**: Visual slide positioning with drag handles

### JavaScript Architecture
- **Class-based**: ImpressEditor main class
- **Event-driven**: Comprehensive event handling
- **State management**: History tracking for undo/redo
- **Modular functions**: Separate methods for each feature

## Export File Specifications

### HTML Structure
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Mi Presentacion</title>
    <style>
        body { background: radial-gradient(rgb(236 202 202), rgb(79 108 136)); }
        .slide-counter { position: fixed; bottom: 20px; right: 20px; font-size: 32px; color: white; background: black; padding: 10px; border-radius: 5px; z-index: 1000; }
        .step:not(.active):not(:has(iframe)):not(:has(canvas)) { opacity: 0.05; }
    </style>
</head>
<body>
    <div id="impress">
        <!-- Generated slides with proper dimensions -->
    </div>
    <script src="https://cdn.jsdelivr.net/gh/impress/impress.js@1.1.0/js/impress.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Counter, chart initialization, and Impress.js setup
    </script>
</body>
</html>
```

### Media Dimensions in Export
- **Iframes**: 90vw x 80vh with rounded borders
- **Images**: 80vw x 60vh with object-fit: contain
- **Charts**: Fixed 800px x 600px canvas size
- **Text slides**: Responsive font sizing based on viewport

### Slide Counter Implementation
- **Position**: Fixed bottom-right (20px margins)
- **Style**: 32px Arial font, white text, black background, rounded corners
- **Format**: "1/13", "2/13", etc.
- **Updates**: Automatically on slide transitions using impress:stepenter event

## Critical Implementation Notes

### Impress.js Version
- **MUST use version 1.1.0** from GitHub CDN: `https://cdn.jsdelivr.net/gh/impress/impress.js@1.1.0/js/impress.min.js`
- **Initialization pattern**:
```javascript
var api = impress();
document.addEventListener('impress:init', function() {
    setTimeout(updateCounter, 1);
});
document.addEventListener('impress:stepenter', updateCounter);
api.init();
```

### Slide Data Structure
```javascript
{
    id: 'unique-id',
    text: 'Slide content',
    x: 0, y: 0, z: 0,
    rotate: 0, scale: 1,
    type: 'slide|title|image|iframe|chart|overview',
    fontFamily: 'Arial, sans-serif',
    fontSize: 48,
    textColor: 'rgb(64, 73, 79)',
    imageUrl: '',
    iframeUrl: '',
    charts: [{
        id: 'chart-id',
        config: { /* Chart.js configuration object */ }
    }]
}
```

### Chart Integration
- **Data source**: Excel (.xlsx) files processed client-side
- **Chart types**: Line, bar, pie, scatter with full customization
- **Color palettes**: 6 predefined schemes with background/border variants
- **Dynamic labels**: Automatic date generation for time series data
- **Export compatibility**: Charts render correctly in exported presentations

### Drag-and-Drop Implementation
- **Canvas positioning**: Convert slide coordinates (x/10, y/10) for display
- **Real-time updates**: Update both visual position and data properties
- **Boundary constraints**: Keep slides within canvas bounds
- **Event handling**: mousedown, mousemove, mouseup pattern

## Known Limitations
- **Iframe navigation**: Interactive websites in iframes are display-only in exported presentations
- **Chart interactivity**: Charts are fully functional in exported files with hover effects and click events
- **File dependencies**: Exported presentations require internet connection for CDN resources
- **Browser compatibility**: Requires modern browser with CSS3 transform support
- **Excel compatibility**: Only .xlsx format supported for chart data import

**Important**: Charts retain full interactivity in exported presentations, while iframes and images are display-only.

## Success Criteria
1. ✅ Complete editor interface with three panels
2. ✅ Drag-and-drop slide positioning on canvas
3. ✅ Real-time property editing
4. ✅ Working preview with animations
5. ✅ Export generates functional standalone HTML
6. ✅ Slide counter visible in exported presentations
7. ✅ All Impress.js animations working correctly
8. ✅ Chart integration with Excel data import
9. ✅ Dynamic charts in exported presentations
10. ✅ Proper media sizing (iframes, images, charts)
11. ✅ Responsive design and error handling
12. ✅ Load existing presentations for editing
13. ✅ Interactive blackboard with drawing tools
14. ✅ Visual transparency for inactive slides
15. ✅ Discrete iconographic design system

## Final Implementation Status
This implementation provides a complete, production-ready Impress.js presentation editor with:
- **Full animation support** in exported presentations
- **Dynamic chart integration** with Excel data import
- **Interactive blackboard functionality** with drawing tools
- **Presentation loading capability** for editing existing files
- **Visual transparency system** for better focus (95% for inactive text slides)
- **Discrete iconographic design** with harmonious visual elements
- **Professional color scheme** with rgb(64, 73, 79) default text color
- **Proper media dimensions** for all slide types
- **Interactive charts** in final presentations
- **Professional export quality** with all features functional

All core functionality is working correctly and the editor is ready for production use with advanced features for professional presentation creation and editing.