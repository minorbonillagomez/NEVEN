# NEVEN Launcher

**Un launcher minimalista y científico para Android**

![NEVEN Logo](docs/logo.png)

## Concepto

NEVEN es un launcher para Android que combina:
- **Funcionalidad** inspirada en Microsoft Launcher
- **Diseño minimalista** inspirado en Niagara Launcher
- **Estética científica** con tipografía LaTeX (Computer Modern)

## Características

### Reloj Científico
El reloj muestra la hora en notación científica con super/subíndices:
```
14³⁰₄₅
```
- Hora: Tamaño título, rojo/color de acento
- Minutos: Superíndice, gris claro
- Segundos: Subíndice, gris oscuro

### Fecha Académica
Siguiendo la jerarquía de papers académicos (Título/Subtítulo/Autor):
```
14³⁰₄₅
Lunes, veintiséis de Octubre
Dos Mil Veintiséis
```

### Paletas de Colores
7 paletas disponibles:
| Paleta | Inspiración |
|--------|-------------|
| Clásico | Académico, rojo |
| Océano | Profundidad, azul |
| Bosque | Naturaleza, verde |
| Ámbar | Calidez, naranja |
| Lavanda | Creatividad, violeta |
| Monocromo | Minimalismo |
| København | Diseño danés, pasteles |

### Idiomas
- Español (es)
- English (en)
- Esperanto (eo)

### Símbolos LaTeX en UI
```
⊚ Configuración    ⊟ Colapsar    ⊞ Expandir
⋒ Menú            ≬ Separador   ↩ Regresar
∴ Más opciones    ∎ Fin/QED     § Sección
```

## Estructura del Proyecto

```
com.neven.launcher/
├── ui/
│   ├── home/          ← Pantalla principal
│   ├── drawer/        ← Lista de apps A-Z
│   ├── search/        ← Búsqueda
│   ├── settings/      ← Configuración
│   ├── notes/         ← Notas con LaTeX
│   ├── components/    ← Componentes reutilizables
│   └── theme/         ← Colores, tipografía
├── widgets/           ← Gestión de widgets
├── services/          ← NotificationListener, etc.
├── latex/             ← Renderizado y formateo
├── data/              ← Repositorios y modelos
└── util/              ← Utilidades
```

## Requisitos

- Android 8.0 (API 26) o superior
- Kotlin 1.9+
- Jetpack Compose

## Configuración de Desarrollo

1. Clonar el repositorio
2. Abrir en Android Studio
3. Descargar fonts Computer Modern y colocar en `app/src/main/res/font/`:
   - `computer_modern_regular.ttf`
   - `computer_modern_bold.ttf`
   - `computer_modern_italic.ttf`
   - `computer_modern_bold_italic.ttf`
4. Sincronizar Gradle
5. Ejecutar en dispositivo/emulador

## Licencia

MIT License

## Créditos

- Tipografía: Computer Modern (Donald Knuth)
- Inspiración: Niagara Launcher, Microsoft Launcher
- Diseño: Estilo académico Elsevier/IEEE
