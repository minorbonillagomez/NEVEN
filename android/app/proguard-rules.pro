# NEVEN Launcher ProGuard Rules

# Keep Compose classes
-keep class androidx.compose.** { *; }

# Keep Room entities
-keep class com.neven.launcher.data.model.** { *; }
