package com.neven.launcher.latex

import java.util.Calendar
import java.util.Locale

/**
 * Formats dates in academic paper style
 * Following the Title/Subtitle/Author hierarchy
 */
object DateFormatter {
    
    /**
     * Returns the day of week in the specified language
     */
    fun getDayOfWeek(calendar: Calendar, locale: Locale): String {
        val dayOfWeek = calendar.get(Calendar.DAY_OF_WEEK)
        return when (locale.language) {
            "es" -> daysSpanish[dayOfWeek - 1]
            "en" -> daysEnglish[dayOfWeek - 1]
            "eo" -> daysEsperanto[dayOfWeek - 1]
            else -> daysEnglish[dayOfWeek - 1]
        }
    }
    
    /**
     * Returns the month name in the specified language
     */
    fun getMonth(calendar: Calendar, locale: Locale): String {
        val month = calendar.get(Calendar.MONTH)
        return when (locale.language) {
            "es" -> monthsSpanish[month]
            "en" -> monthsEnglish[month]
            "eo" -> monthsEsperanto[month]
            else -> monthsEnglish[month]
        }
    }
    
    /**
     * Returns the day number as ordinal text
     * e.g., "veintiséis", "twenty-sixth", "dudek-sesa"
     */
    fun getDayOrdinal(calendar: Calendar, locale: Locale): String {
        val day = calendar.get(Calendar.DAY_OF_MONTH)
        return when (locale.language) {
            "es" -> NumberToWords.convert(day, locale)
            "en" -> getEnglishOrdinal(day)
            "eo" -> getEsperantoOrdinal(day)
            else -> getEnglishOrdinal(day)
        }
    }
    
    /**
     * Returns the year in words
     * e.g., "Dos Mil Veintiséis", "Two Thousand Twenty-Six", "Du Mil Dudek Ses"
     */
    fun getYearInWords(calendar: Calendar, locale: Locale): String {
        val year = calendar.get(Calendar.YEAR)
        return NumberToWords.capitalizeWords(NumberToWords.convert(year, locale))
    }
    
    /**
     * Returns the complete formatted date line
     * Format varies by language:
     * - es: "Lunes, veintiséis de Octubre"
     * - en: "Monday, October twenty-sixth"  
     * - eo: "Lundo, la dudek-sesa de Oktobro"
     */
    fun getFormattedDate(calendar: Calendar, locale: Locale): String {
        val dayOfWeek = getDayOfWeek(calendar, locale)
        val day = getDayOrdinal(calendar, locale)
        val month = getMonth(calendar, locale)
        
        return when (locale.language) {
            "es" -> "$dayOfWeek, $day de $month"
            "en" -> "$dayOfWeek, $month $day"
            "eo" -> "$dayOfWeek, la $day de $month"
            else -> "$dayOfWeek, $month $day"
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // Days of Week
    // ═══════════════════════════════════════════════════════════════
    private val daysSpanish = listOf(
        "Domingo", "Lunes", "Martes", "Miércoles", 
        "Jueves", "Viernes", "Sábado"
    )
    
    private val daysEnglish = listOf(
        "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    )
    
    private val daysEsperanto = listOf(
        "Dimanĉo", "Lundo", "Mardo", "Merkredo",
        "Ĵaŭdo", "Vendredo", "Sabato"
    )
    
    // ═══════════════════════════════════════════════════════════════
    // Months
    // ═══════════════════════════════════════════════════════════════
    private val monthsSpanish = listOf(
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )
    
    private val monthsEnglish = listOf(
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    )
    
    private val monthsEsperanto = listOf(
        "Januaro", "Februaro", "Marto", "Aprilo", "Majo", "Junio",
        "Julio", "Aŭgusto", "Septembro", "Oktobro", "Novembro", "Decembro"
    )
    
    // ═══════════════════════════════════════════════════════════════
    // Ordinal Helpers
    // ═══════════════════════════════════════════════════════════════
    private fun getEnglishOrdinal(day: Int): String {
        val cardinal = NumberToWords.convert(day, Locale.ENGLISH).lowercase()
        
        // Handle special cases for ordinals
        return when {
            day == 1 -> "first"
            day == 2 -> "second"
            day == 3 -> "third"
            day == 5 -> "fifth"
            day == 8 -> "eighth"
            day == 9 -> "ninth"
            day == 12 -> "twelfth"
            day in 11..13 -> "${cardinal}th"
            day % 10 == 1 -> cardinal.dropLast(1) + "first"
            day % 10 == 2 -> cardinal.dropLast(1) + "second"  
            day % 10 == 3 -> cardinal.dropLast(1) + "third"
            cardinal.endsWith("y") -> cardinal.dropLast(1) + "ieth"
            cardinal.endsWith("e") -> cardinal.dropLast(1) + "th"
            else -> "${cardinal}th"
        }
    }
    
    private fun getEsperantoOrdinal(day: Int): String {
        // In Esperanto, ordinals use -a suffix
        val cardinal = NumberToWords.convert(day, Locale("eo"))
        return when {
            day < 10 -> "${cardinal}a"
            else -> {
                // For compound numbers like "dudek ses" -> "dudek-sesa"
                val parts = cardinal.split(" ")
                if (parts.size == 1) {
                    "${cardinal}a"
                } else {
                    "${parts.dropLast(1).joinToString("-")}-${parts.last()}a"
                }
            }
        }
    }
}
