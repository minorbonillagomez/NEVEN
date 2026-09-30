# Sistema de Bitácora NEVEN

## Estructura

```
.kiro/contexto/
├── CHAT.md              # Bitácora activa (sesiones recientes, <60KB)
├── README.md            # Este archivo
├── Notebooklm.md        # Notas para NotebookLM
└── archivo/
    ├── 2026-08-historico.md    # Historial detallado agosto 2026
    └── CHAT-backup-*.md        # Backups automáticos
```

## Uso

### Al iniciar sesión
1. Kiro lee `CHAT.md` (ligero, carga rápida)
2. Si necesita contexto histórico, busca en `archivo/`

### Al cerrar sesión  
1. Kiro agrega resumen a `CHAT.md`
2. Mensualmente, el contenido viejo se archiva

### Búsqueda histórica
- Usar grep en `archivo/` para buscar sesiones antiguas
- Cada archivo mensual tiene formato consistente

## Convenciones

### Formato de entrada
```markdown
### [Sesión YYYY-MM-DD ~HH:MM] Descripción breve

## 🔧/🐛/✅ TÍTULO DEL LOGRO

### Problema/Logro
...

### Archivos modificados
| Archivo | Cambio |
|---------|--------|

### Commits
| Hash | Descripción |
|------|-------------|

### Pendientes
| Prioridad | Tarea |
|-----------|-------|
```

### Prioridades
- **ALTA** — Bloquea trabajo o afecta producción
- **MEDIA** — Mejora importante pero no urgente
- **BAJA** — Nice-to-have, cleanup, documentación

## Mantenimiento

### Archivar mensualmente
Cuando `CHAT.md` supere ~100KB:
1. Mover contenido antiguo a `archivo/YYYY-MM.md`
2. Dejar solo últimas 5-10 sesiones en `CHAT.md`
3. Actualizar tabla de índice en `CHAT.md`

### Backups
Los backups automáticos (`CHAT-backup-*.md`) pueden eliminarse después de verificar que el archivo principal está correcto.
