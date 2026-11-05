# NEVEN Launcher - Guía de Configuración

## Abrir en Android Studio

1. **Abrir Android Studio**
2. **File → Open**
3. Navegar a: `C:\Users\Minor Bonilla G\Desktop\PHP\NEVEN`
4. Hacer clic en **Open**
5. Esperar a que Gradle sincronice (puede tomar unos minutos)

## Requisitos Previos

- Android Studio Hedgehog (2023.1) o superior
- JDK 17
- Android SDK 34
- Gradle 8.2

## Configuración del AVD (Emulador)

Para probar NEVEN, recomiendo crear un emulador Pixel:

1. **Tools → Device Manager**
2. **Create Device**
3. Seleccionar **Pixel 7 Pro** o **Pixel 8 Pro**
4. System Image: **API 34** (Android 14)
5. Finalizar y ejecutar

## Ejecutar el Launcher

1. Conectar dispositivo físico o iniciar emulador
2. Click en **Run** (▶) o `Shift+F10`
3. Seleccionar dispositivo
4. Después de instalar, ir a **Settings → Apps → Default apps → Home app**
5. Seleccionar **NEVEN**

## Estructura del Proyecto

```
NEVEN/
├── app/
│   ├── build.gradle.kts
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── java/com/neven/launcher/
│       │   ├── NevenApplication.kt
│       │   ├── ui/
│       │   │   ├── home/           ← Pantalla principal
│       │   │   ├── drawer/         ← Lista de apps A-Z
│       │   │   ├── settings/       ← Configuración
│       │   │   ├── components/     ← Reloj científico
│       │   │   └── theme/          ← Colores y tipografía
│       │   ├── latex/              ← Formateo de fechas/números
│       │   └── services/           ← Notificaciones
│       └── res/
│           ├── values/             ← Español
│           ├── values-en/          ← English
│           ├── values-eo/          ← Esperanto
│           └── mipmap-*/           ← Logo NEVEN
├── build.gradle.kts
├── settings.gradle.kts
└── README.md
```

## Funcionalidades Implementadas

| Feature | Estado | Archivo |
|---------|--------|---------|
| Reloj científico (HH^mm_ss) | ✅ | ScientificClock.kt |
| 7 paletas de colores | ✅ | Color.kt |
| 3 idiomas (ES/EN/EO) | ✅ | strings.xml |
| App Drawer vertical | ✅ | AppDrawerScreen.kt |
| Alfabeto lateral | ✅ | AppDrawerScreen.kt |
| Notification badges | ✅ | NotificationListenerService.kt |
| Settings screen | ✅ | SettingsScreen.kt |
| Logo oficial | ✅ | mipmap-*/ic_launcher.png |

## Próximos Pasos (Pendientes)

1. **Widgets** - Implementar WidgetHostManager
2. **Notas LaTeX** - Editor con renderizado de fórmulas
3. **Búsqueda** - SearchActivity
4. **DataStore** - Persistir preferencias
5. **Gestos** - Swipe para abrir drawer

## Solución de Problemas

### Error de Gradle Sync
```
File → Invalidate Caches → Invalidate and Restart
```

### Fonts no encontrados
El proyecto usa `FontFamily.Serif` como fallback. Para usar Computer Modern:
1. Descargar de https://www.fontsquirrel.com/fonts/computer-modern
2. Colocar .ttf en `app/src/main/res/font/`
3. Actualizar `Type.kt`

### El launcher no aparece en la lista
Verificar que `AndroidManifest.xml` tenga:
```xml
<category android:name="android.intent.category.HOME" />
<category android:name="android.intent.category.DEFAULT" />
```

---

**NEVEN** - Launcher Científico para Android
*Tipografía LaTeX • Diseño Minimalista • Espíritu Académico*
