package com.neven.launcher.latex

import java.util.Locale

/**
 * Converts numbers to words in multiple languages
 * Supports: Spanish (es), English (en), Esperanto (eo)
 */
object NumberToWords {
    
    fun convert(number: Int, locale: Locale): String {
        return when (locale.language) {
            "es" -> convertSpanish(number)
            "en" -> convertEnglish(number)
            "eo" -> convertEsperanto(number)
            else -> convertEnglish(number) // fallback
        }
    }
    
    // ═══════════════════════════════════════════════════════════════
    // SPANISH
    // ═══════════════════════════════════════════════════════════════
    private fun convertSpanish(number: Int): String {
        if (number == 0) return "cero"
        if (number < 0) return "menos ${convertSpanish(-number)}"
        
        return when {
            number < 16 -> unitsSpanish[number]
            number < 20 -> "dieci${unitsSpanish[number - 10]}"
            number < 30 -> if (number == 20) "veinte" 
                          else "veinti${unitsSpanish[number - 20]}"
            number < 100 -> {
                val tens = number / 10
                val units = number % 10
                if (units == 0) tensSpanish[tens]
                else "${tensSpanish[tens]} y ${unitsSpanish[units]}"
            }
            number < 1000 -> {
                val hundreds = number / 100
                val remainder = number % 100
                val hundredWord = when {
                    hundreds == 1 && remainder == 0 -> "cien"
                    hundreds == 1 -> "ciento"
                    hundreds == 5 -> "quinientos"
                    hundreds == 7 -> "setecientos"
                    hundreds == 9 -> "novecientos"
                    else -> "${unitsSpanish[hundreds]}cientos"
                }
                if (remainder == 0) hundredWord
                else "$hundredWord ${convertSpanish(remainder)}"
            }
            number < 1_000_000 -> {
                val thousands = number / 1000
                val remainder = number % 1000
                val thousandWord = if (thousands == 1) "mil" 
                                   else "${convertSpanish(thousands)} mil"
                if (remainder == 0) thousandWord
                else "$thousandWord ${convertSpanish(remainder)}"
            }
            else -> number.toString()
        }
    }
    
    private val unitsSpanish = listOf(
        "", "uno", "dos", "tres", "cuatro", "cinco", 
        "seis", "siete", "ocho", "nueve", "diez",
        "once", "doce", "trece", "catorce", "quince"
    )
    
    private val tensSpanish = listOf(
        "", "", "veinte", "treinta", "cuarenta", "cincuenta",
        "sesenta", "setenta", "ochenta", "noventa"
    )
    
    // ═══════════════════════════════════════════════════════════════
    // ENGLISH
    // ═══════════════════════════════════════════════════════════════
    private fun convertEnglish(number: Int): String {
        if (number == 0) return "Zero"
        if (number < 0) return "Minus ${convertEnglish(-number)}"
        
        return when {
            number < 20 -> unitsEnglish[number]
            number < 100 -> {
                val tens = number / 10
                val units = number % 10
                if (units == 0) tensEnglish[tens]
                else "${tensEnglish[tens]}-${unitsEnglish[units].lowercase()}"
            }
            number < 1000 -> {
                val hundreds = number / 100
                val remainder = number % 100
                val hundredWord = "${unitsEnglish[hundreds]} Hundred"
                if (remainder == 0) hundredWord
                else "$hundredWord ${convertEnglish(remainder)}"
            }
            number < 1_000_000 -> {
                val thousands = number / 1000
                val remainder = number % 1000
                val thousandWord = "${convertEnglish(thousands)} Thousand"
                if (remainder == 0) thousandWord
                else "$thousandWord ${convertEnglish(remainder)}"
            }
            else -> number.toString()
        }
    }
    
    private val unitsEnglish = listOf(
        "", "One", "Two", "Three", "Four", "Five",
        "Six", "Seven", "Eight", "Nine", "Ten",
        "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
        "Sixteen", "Seventeen", "Eighteen", "Nineteen"
    )
    
    private val tensEnglish = listOf(
        "", "", "Twenty", "Thirty", "Forty", "Fifty",
        "Sixty", "Seventy", "Eighty", "Ninety"
    )
    
    // ═══════════════════════════════════════════════════════════════
    // ESPERANTO
    // ═══════════════════════════════════════════════════════════════
    private fun convertEsperanto(number: Int): String {
        if (number == 0) return "nulo"
        if (number < 0) return "minus ${convertEsperanto(-number)}"
        
        return when {
            number < 10 -> unitsEsperanto[number]
            number < 100 -> {
                val tens = number / 10
                val units = number % 10
                val tensWord = if (tens == 1) "dek" else "${unitsEsperanto[tens]}dek"
                if (units == 0) tensWord
                else "$tensWord ${unitsEsperanto[units]}"
            }
            number < 1000 -> {
                val hundreds = number / 100
                val remainder = number % 100
                val hundredWord = if (hundreds == 1) "cent" 
                                  else "${unitsEsperanto[hundreds]}cent"
                if (remainder == 0) hundredWord
                else "$hundredWord ${convertEsperanto(remainder)}"
            }
            number < 1_000_000 -> {
                val thousands = number / 1000
                val remainder = number % 1000
                val thousandWord = if (thousands == 1) "mil" 
                                   else "${convertEsperanto(thousands)} mil"
                if (remainder == 0) thousandWord
                else "$thousandWord ${convertEsperanto(remainder)}"
            }
            else -> number.toString()
        }
    }
    
    private val unitsEsperanto = listOf(
        "", "unu", "du", "tri", "kvar", "kvin",
        "ses", "sep", "ok", "naŭ"
    )
    
    // ═══════════════════════════════════════════════════════════════
    // Helper: Capitalize first letter of each word
    // ═══════════════════════════════════════════════════════════════
    fun capitalizeWords(text: String): String {
        return text.split(" ").joinToString(" ") { word ->
            word.replaceFirstChar { 
                if (it.isLowerCase()) it.titlecase() else it.toString() 
            }
        }
    }
}
