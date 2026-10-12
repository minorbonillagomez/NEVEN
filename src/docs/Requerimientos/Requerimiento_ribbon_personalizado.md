# Requerimiento Detallado: Ribbon Personalizado e Integración Visual (UI/UX)

## 1. Visión General y Objetivo
El backend computacional (aislamiento, motores R/Julia, protocolo IPC y Callback Thread) de NEVEN se encuentra en un estado funcional avanzado y estable. El siguiente paso crítico para alcanzar la calificación de excelencia absoluta (10/10) es dotar al proyecto de una interfaz gráfica nativa en Excel. 

El **objetivo** de este requerimiento es definir la especificación funcional y técnica para el diseño y desarrollo de un *Ribbon Personalizado* (cinta de opciones) en Excel. Esta pestaña centralizará todas las interacciones del usuario con la plataforma, elevando la experiencia de usuario (UX) mediante el concepto de **biomimesis**, garantizando que las herramientas avanzadas de ciencia de datos se perciban y operen como capacidades nativas de Excel.

## 2. Alcance
- Creación de una pestaña exclusiva denominada **"NEVEN"** en la cinta de opciones principal de Excel.
- Implementación del archivo XML de definición de interfaz (CustomUI).
- Integración en C++ mediante interfaces COM (`IRibbonExtensibility`, `IRibbonUI`) para manejar la carga de la interfaz y los eventos (callbacks) de los botones.
- Diseño de la identidad gráfica (iconografía y ventanas modales) alineada con los estándares de diseño corporativo moderno.

## 3. Arquitectura Visual (Elementos de la Interfaz)
El Ribbon estará dividido en grupos lógicos de comandos para facilitar la navegación del usuario.

### Grupo 1: Consolas y Entornos
- **Consola R:** Botón de tamaño grande para abrir la interfaz REPL interactiva de R.
- **Consola Julia:** Botón de tamaño grande para abrir la interfaz interactiva de Julia.
- **Visor Pluto.jl:** Lanzador del servidor de Pluto y apertura del visor web embebido (WebView2).

### Grupo 2: Gestión de Código
- **Actualizar Funciones (Hot-Reload):** Botón para forzar la recarga de todos los scripts (`.R` y `.jl`) del directorio de trabajo y registrar/actualizar inmediatamente las fórmulas en el asistente de Excel.
- **Directorio de Scripts:** Botón de acción rápida que abre el explorador de Windows directamente en la carpeta donde residen los scripts del usuario (`NEVEN-scripts`).

### Grupo 3: Reportes y Publicación (Quarto)
- **Renderizar Documento:** Botón que busca y compila documentos `.qmd` asociados al proyecto activo en Excel para la generación automática de HTML/PDF/Word.
- **Presentation Builder:** Herramienta para enviar gráficos o rangos de Excel seleccionados hacia presentaciones de reveal.js.

### Grupo 4: Configuración y Ayuda
- **Configuración JSON:** Botón que abre el archivo de control `neven-config.json` en el editor predeterminado del sistema (VS Code, Notepad, etc.).
- **Documentación:** Enlace que abre el manual del usuario y guías en el navegador web predeterminado.
- **Acerca de (About):** Botón que despliega una ventana de diálogo modal (WinForms/WPF embebido o caja de diálogo Win32) con:
  - Logotipo vectorial del proyecto.
  - Versión de compilación de NEVEN, versión instalada de R y versión instalada de Julia.
  - Créditos, licencia de código abierto y afiliación (Universidad de Costa Rica).
  - Indicadores de estado en tiempo real (Puntos de luz verde/rojo para la conexión IPC de R y Julia).

## 4. Requerimientos Técnicos
1. **Definición XML CustomUI:** El layout del Ribbon debe construirse utilizando el esquema XML `customUI14` (Office 2010 en adelante).
2. **Implementación de Interfaces COM:** 
   - La clase principal de registro del XLL debe heredar o implementar la interfaz `IRibbonExtensibility`.
   - Sobrescribir el método `GetCustomUI` para servir el string XML en tiempo de carga de Excel.
   - Capturar el objeto `IRibbonUI` en el callback `onLoad` para permitir actualizaciones dinámicas (ej. invalidar controles para cambiar el estado visual de los botones si falla un motor computacional).
3. **Gestión Concurrente de Callbacks:** Los eventos `onAction` invocados por el usuario deben enrutarse hacia C++. Debido a que la interacción con R/Julia se realiza asincrónicamente mediante *Named Pipes*, los comandos del Ribbon deben aprovechar la arquitectura estable de hilos para no congelar la interfaz de Excel.
4. **Gestión de Recursos (Imágenes):** Las imágenes deben compilarse en el archivo de recursos `.rc` e inyectarse nativamente mediante el callback `getImage`. Los archivos base deben ser PNG de alta resolución (mínimo 64x64) preservando el canal Alpha (transparencias).

## 5. Diseño e Identidad Visual (UI/UX)
- **Estética "Premium":** El diseño debe proyectar autoridad técnica y simplicidad, dirigido al "Citizen Data Scientist". No debe parecer un complemento sobrecargado.
- **Iconografía:** Utilizar paletas de colores representativas pero modernizadas (Flat/Fluent Design):
  - **R:** Azul metálico/Acero.
  - **Julia:** Colores primarios de la marca (Verde, Rojo, Púrpura).
  - **Quarto/Pluto:** Logotipos oficiales limpios sin fondos.
- **Supertips (Tooltips enriquecidos):** Todos los controles del Ribbon deben poseer etiquetas `<supertip>` que ofrezcan una guía instantánea (ej. en el botón *Actualizar*: *"Recarga las definiciones en R y Julia de su carpeta de proyecto, incorporándolas como fórmulas nativas en esta sesión"*).

## 6. Casos de Uso y Flujos
- **Flujo de Trabajo Típico:** El usuario escribe código en su IDE favorito, cambia a Excel y presiona el botón de **"Actualizar Funciones"** en el Ribbon, viendo los resultados reflejados inmediatamente.
- **Auditoría:** Ante un fallo inesperado de la hoja de cálculo, el usuario hace clic en **"Acerca de"** para verificar rápidamente a través de los indicadores LED simulados si R o Julia han colapsado en el proceso de fondo.

## 7. Criterios de Aceptación (QA)
- [ ] La pestaña "NEVEN" se integra fluidamente al inicio de Excel sin generar errores de sintaxis XML en la consola de depuración de Office.
- [ ] Los botones mapean correctamente a la funcionalidad sin cuelgues (crashes).
- [ ] Las imágenes respetan canal Alpha y se ven correctas tanto en el modo claro como en el modo oscuro (Dark Theme) de Microsoft Office 365.
- [ ] La ventana de "Acerca de" lee dinámicamente las variables de entorno de versión y conexión.
- [ ] No existen fugas de memoria (memory leaks) asociadas a objetos de recursos GDI+ o referencias COM no liberadas tras el cierre del programa.
