package com.neven.launcher.data

import java.util.UUID

/**
 * Colores disponibles para los Post-it
 * Paleta cientifica/academica
 */
enum class StickyNoteColor(val hex: String, val displayName: String) {
    YELLOW("#FFF59D", "Amarillo"),      // Clasico post-it
    CREAM("#FFF8E1", "Crema"),          // Papel antiguo
    BLUE("#BBDEFB", "Azul"),            // Azul cielo
    GREEN("#C8E6C9", "Verde"),          // Verde menta
    PINK("#F8BBD9", "Rosa"),            // Rosa suave
    ORANGE("#FFCC80", "Naranja"),       // Naranja pastel
    PURPLE("#E1BEE7", "Lavanda"),       // Lavanda
    WHITE("#FAFAFA", "Blanco")          // Papel blanco
}

/**
 * Tamanos predefinidos para los Post-it
 */
enum class StickyNoteSize(val widthDp: Int, val heightDp: Int, val displayName: String) {
    SMALL(120, 120, "Pequeno"),
    MEDIUM(160, 160, "Mediano"),
    LARGE(200, 200, "Grande"),
    WIDE(240, 140, "Ancho"),
    TALL(140, 240, "Alto")
}

/**
 * Modelo de un Post-it / Nota adhesiva
 */
data class StickyNote(
    val id: String = UUID.randomUUID().toString(),
    val pageIndex: Int,           // Pagina del pager donde esta la nota
    val content: String = "",     // Contenido Markdown
    val positionX: Float = 0f,    // Posicion X relativa (0-1)
    val positionY: Float = 0f,    // Posicion Y relativa (0-1)
    val color: StickyNoteColor = StickyNoteColor.YELLOW,
    val size: StickyNoteSize = StickyNoteSize.MEDIUM,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    val zIndex: Int = 0           // Para ordenar capas cuando se superponen
) {
    /**
     * Crea una copia actualizada con nuevo contenido
     */
    fun withContent(newContent: String): StickyNote {
        return copy(
            content = newContent,
            updatedAt = System.currentTimeMillis()
        )
    }
    
    /**
     * Crea una copia con nueva posicion
     */
    fun withPosition(x: Float, y: Float): StickyNote {
        return copy(
            positionX = x.coerceIn(0f, 1f),
            positionY = y.coerceIn(0f, 1f),
            updatedAt = System.currentTimeMillis()
        )
    }
    
    /**
     * Crea una copia con nuevo color
     */
    fun withColor(newColor: StickyNoteColor): StickyNote {
        return copy(
            color = newColor,
            updatedAt = System.currentTimeMillis()
        )
    }
    
    /**
     * Crea una copia con nuevo tamano
     */
    fun withSize(newSize: StickyNoteSize): StickyNote {
        return copy(
            size = newSize,
            updatedAt = System.currentTimeMillis()
        )
    }
    
    /**
     * Serializa a string para DataStore
     * Usa ␞ (Unicode Unit Separator) como delimitador seguro
     */
    fun serialize(): String {
        val separator = "\u001E" // Unit Separator - caracter de control seguro
        return listOf(
            id,
            pageIndex.toString(),
            // Escapar el separador si aparece en el contenido (muy raro)
            content.replace(separator, "\\u001E"),
            positionX.toString(),
            positionY.toString(),
            color.name,
            size.name,
            createdAt.toString(),
            updatedAt.toString(),
            zIndex.toString()
        ).joinToString(separator)
    }
    
    companion object {
        /**
         * Deserializa desde string de DataStore
         */
        fun deserialize(data: String): StickyNote? {
            return try {
                val separator = "\u001E"
                val parts = data.split(separator)
                if (parts.size < 10) {
                    // Intentar formato antiguo con |
                    return deserializeOldFormat(data)
                }
                
                StickyNote(
                    id = parts[0],
                    pageIndex = parts[1].toInt(),
                    content = parts[2].replace("\\u001E", separator),
                    positionX = parts[3].toFloat(),
                    positionY = parts[4].toFloat(),
                    color = StickyNoteColor.valueOf(parts[5]),
                    size = StickyNoteSize.valueOf(parts[6]),
                    createdAt = parts[7].toLong(),
                    updatedAt = parts[8].toLong(),
                    zIndex = parts[9].toInt()
                )
            } catch (e: Exception) {
                null
            }
        }
        
        /**
         * Deserializa formato antiguo (para compatibilidad)
         */
        private fun deserializeOldFormat(data: String): StickyNote? {
            return try {
                // Formato antiguo usaba | como separador
                val parts = data.split("|")
                if (parts.size < 10) return null
                
                StickyNote(
                    id = parts[0],
                    pageIndex = parts[1].toInt(),
                    content = parts[2].replace("\\n", "\n").replace("\\|", "|"),
                    positionX = parts[3].toFloat(),
                    positionY = parts[4].toFloat(),
                    color = StickyNoteColor.valueOf(parts[5]),
                    size = StickyNoteSize.valueOf(parts[6]),
                    createdAt = parts[7].toLong(),
                    updatedAt = parts[8].toLong(),
                    zIndex = parts[9].toInt()
                )
            } catch (e: Exception) {
                null
            }
        }
    }
}
