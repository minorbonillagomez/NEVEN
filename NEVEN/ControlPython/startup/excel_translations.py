# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN v3.0 — Excel Function Translations
# ═══════════════════════════════════════════════════════════════════════════════
# Maps localized Excel function names to English equivalents.
# Excel uses different function names depending on the installation language.
#
# Source: PerfectXL function translations
# https://www.perfectxl.com/academy/functions/translations/
#
# Usage:
#   from excel_translations import normalize_formula, get_english_name
#   english_name = get_english_name("BUSCARV", "es")  # Returns "VLOOKUP"
#   normalized = normalize_formula("=SI(BUSCARV(A1,B:C,2,0)>0,1,0)", "es")
# ═══════════════════════════════════════════════════════════════════════════════

import re
from typing import Optional

# ─── Spanish to English translations ──────────────────────────────────────────
# Complete mapping of Spanish Excel function names to English equivalents

SPANISH_TO_ENGLISH = {
    # A
    "ABS": "ABS",
    "ACOS": "ACOS",
    "ACOSH": "ACOSH",
    "ACOT": "ACOT",
    "ACOTH": "ACOTH",
    "AGREGAR": "AGGREGATE",
    "AHORA": "NOW",
    "ALEATORIO": "RAND",
    "ALEATORIO.ENTRE": "RANDBETWEEN",
    "AMORTIZ.LIN": "AMORLINC",
    "AMORTIZ.PROGRE": "AMORDEGRC",
    "AÑO": "YEAR",
    "AREAS": "AREAS",
    "ASC": "ASC",
    "ASENO": "ASIN",
    "ASENOH": "ASINH",
    "ATAN": "ATAN",
    "ATAN2": "ATAN2",
    "ATANH": "ATANH",
    # B
    "BASE": "BASE",
    "BDCONTAR": "DCOUNT",
    "BDCONTARA": "DCOUNTA",
    "BDDESVEST": "DSTDEV",
    "BDDESVESTP": "DSTDEVP",
    "BDEXTRAER": "DGET",
    "BDMAX": "DMAX",
    "BDMIN": "DMIN",
    "BDPRODUCTO": "DPRODUCT",
    "BDPROMEDIO": "DAVERAGE",
    "BDSUMA": "DSUM",
    "BDVAR": "DVAR",
    "BDVARP": "DVARP",
    "BESSELI": "BESSELI",
    "BESSELJ": "BESSELJ",
    "BESSELK": "BESSELK",
    "BESSELY": "BESSELY",
    "BIN.A.DEC": "BIN2DEC",
    "BIN.A.HEX": "BIN2HEX",
    "BIN.A.OCT": "BIN2OCT",
    "BINOM.CRIT": "CRITBINOM",
    "BIT.DESPLIZQDA": "BITLSHIFT",
    "BIT.XO": "BITXOR",
    "BIT.Y": "BITAND",
    "BITOR": "BITOR",
    "BITRSHIFT": "BITRSHIFT",
    "BUSCAR": "LOOKUP",
    "BUSCARH": "HLOOKUP",
    "BUSCARV": "VLOOKUP",
    "BUSCARX": "XLOOKUP",
    # C
    "CANTIDAD.RECIBIDA": "RECEIVED",
    "CARACTER": "CHAR",
    "CEILING.MATH": "CEILING.MATH",
    "CELDA": "CELL",
    "COCIENTE": "QUOTIENT",
    "CODIGO": "CODE",
    "COEF.DE.CORREL": "CORREL",
    "COEFICIENTE.ASIMETRIA": "SKEW",
    "COEFICIENTE.ASIMETRIA.P": "SKEW.P",
    "COEFICIENTE.R2": "RSQ",
    "COINCIDIR": "MATCH",
    "COLUMNA": "COLUMN",
    "COLUMNAS": "COLUMNS",
    "COMBINA": "COMBINA",
    "COMBINAT": "COMBIN",
    "COMPLEJO": "COMPLEX",
    "CONCATENAR": "CONCATENATE",
    "CONJUNTO.CUBO": "CUBESET",
    "CONTAR": "COUNT",
    "CONTAR.BLANCO": "COUNTBLANK",
    "CONTAR.SI": "COUNTIF",
    "CONTAR.SI.CONJUNTO": "COUNTIFS",
    "CONTARA": "COUNTA",
    "CONV.DECIMAL": "DECIMAL",
    "CONVERTIR": "CONVERT",
    "COS": "COS",
    "COSH": "COSH",
    "COT": "COT",
    "COTH": "COTH",
    "COVAR": "COVAR",
    "COVARIANZA.M": "COVARIANCE.S",
    "COVARIANZA.P": "COVARIANCE.P",
    "CRECIMIENTO": "GROWTH",
    "CSC": "CSC",
    "CSCH": "CSCH",
    "CUARTIL": "QUARTILE",
    "CUARTIL.EXC": "QUARTILE.EXC",
    "CUARTIL.INC": "QUARTILE.INC",
    "CUPON.DIAS": "COUPDAYS",
    "CUPON.DIAS.L1": "COUPDAYBS",
    "CUPON.DIAS.L2": "COUPDAYSNC",
    "CUPON.FECHA.L1": "COUPPCD",
    "CUPON.FECHA.L2": "COUPNCD",
    "CUPON.NUM": "COUPNUM",
    "CURTOSIS": "KURTOSIS",
    # D
    "DB": "DB",
    "DBCS": "DBCS",
    "DDB": "DDB",
    "DEC.A.BIN": "DEC2BIN",
    "DEC.A.HEX": "DEC2HEX",
    "DEC.A.OCT": "DEC2OCT",
    "DELTA": "DELTA",
    "DERECHA": "RIGHT",
    "DERECHAB": "RIGHTB",
    "DESREF": "OFFSET",
    "DESVEST": "STDEV",
    "DESVEST.M": "STDEV.S",
    "DESVEST.P": "STDEV.P",
    "DESVESTA": "STDEVA",
    "DESVESTP": "STDEVP",
    "DESVESTPA": "STDEVPA",
    "DESVIA2": "DEVSQ",
    "DESVPROM": "AVEDEV",
    "DIA": "DAY",
    "DIA.LAB": "WORKDAY",
    "DIA.LAB.INTL": "WORKDAY.INTL",
    "DIAS": "DAYS",
    "DIAS.LAB": "NETWORKDAYS",
    "DIAS.LAB.INTL": "NETWORKDAYS.INTL",
    "DIAS360": "DAYS360",
    "DIASEM": "WEEKDAY",
    "DIRECCION": "ADDRESS",
    "DIST.WEIBULL": "WEIBULL.DIST",
    "DISTR.BETA": "BETA.DIST",
    "DISTR.BETA.INV": "BETAINV",
    "DISTR.BINOM": "BINOMDIST",
    "DISTR.BINOM.N": "BINOM.DIST",
    "DISTR.BINOM.SERIE": "BINOM.DIST.RANGE",
    "DISTR.CHI": "CHIDIST",
    "DISTR.CHICUAD": "CHISQ.DIST",
    "DISTR.CHICUAD.CD": "CHISQ.DIST.RT",
    "DISTR.EXP": "EXPONDIST",
    "DISTR.EXP.N": "EXPON.DIST",
    "DISTR.F": "FDIST",
    "DISTR.F.CD": "F.DIST.RT",
    "DISTR.F.INV": "FINV",
    "DISTR.F.RT": "F.DIST",
    "DISTR.GAMMA": "GAMMADIST",
    "DISTR.GAMMA.INV": "GAMMAINV",
    "DISTR.GAMMA.N": "GAMMA.DIST",
    "DISTR.HIPERGEOM": "HYPGEOMDIST",
    "DISTR.HIPERGEOM.N": "HYPGEOM.DIST",
    "DISTR.LOG.INV": "LOGINV",
    "DISTR.LOG.NORM": "LOGNORMDIST",
    "DISTR.LOGNORM": "LOGNORM.DIST",
    "DISTR.NORM": "NORMDIST",
    "DISTR.NORM.ESTAND": "NORMSDIST",
    "DISTR.NORM.ESTAND.INV": "NORMSINV",
    "DISTR.NORM.ESTAND.N": "NORM.S.DIST",
    "DISTR.NORM.INV": "NORMINV",
    "DISTR.NORM.N": "NORM.DIST",
    "DISTR.T": "TDIST",
    "DISTR.T.2C": "T.DIST.2T",
    "DISTR.T.CD": "T.DIST.RT",
    "DISTR.T.INV": "TINV",
    "DISTR.T.N": "T.DIST",
    "DURACION": "DURATION",
    "DURACION.MODIF": "MDURATION",
    "DVS": "VDB",
    # E
    "ELEGIR": "CHOOSE",
    "ENCONTRAR": "FIND",
    "ENCONTRARB": "FINDB",
    "ENTERO": "INT",
    "ERROR.TIPICO.XY": "STEYX",
    "ES.IMPAR": "ISODD",
    "ES.PAR": "ISEVEN",
    "ESBLANCO": "ISBLANK",
    "ESERR": "ISERR",
    "ESERROR": "ISERROR",
    "ESFORMULA": "ISFORMULA",
    "ESLOGICO": "ISLOGICAL",
    "ESNOD": "ISNA",
    "ESNOTEXTO": "ISNONTEXT",
    "ESNUMERO": "ISNUMBER",
    "ESPACIOS": "TRIM",
    "ESREF": "ISREF",
    "ESTEXTO": "ISTEXT",
    "ESTIMACION.LINEAL": "LINEST",
    "ESTIMACION.LOGARITMICA": "LOGEST",
    "EUROCONVERT": "EUROCONVERT",
    "EXP": "EXP",
    "EXTRAE": "MID",
    "EXTRAEB": "MIDB",
    # F
    "FACT": "FACT",
    "FACT.DOBLE": "FACTDOUBLE",
    "FALSO": "FALSE",
    "FECHA": "DATE",
    "FECHA.MES": "EDATE",
    "FECHANUMERO": "DATEVALUE",
    "FI": "PHI",
    "FILA": "ROW",
    "FILAS": "ROWS",
    "FIN.MES": "EOMONTH",
    "FISHER": "FISHER",
    "FONETICO": "PHONETIC",
    "FORMULATEXTO": "FORMULATEXT",
    "FRAC.AÑO": "YEARFRAC",
    "FRECUENCIA": "FREQUENCY",
    "FUN.ERROR": "ERF",
    "FUN.ERROR.COMPL": "ERFC",
    "FUN.ERROR.COMPL.EXACTO": "ERFC.PRECISE",
    "FUN.ERROR.EXACTO": "ERF.PRECISE",
    # G
    "GAMMA": "GAMMA",
    "GAMMA.LN": "GAMMALN",
    "GAMMA.LN.EXACTO": "GAMMALN.PRECISE",
    "GAUSS": "GAUSS",
    "GRADOS": "DEGREES",
    # H
    "HALLAR": "SEARCH",
    "HALLARB": "SEARCHB",
    "HEX.A.BIN": "HEX2BIN",
    "HEX.A.DEC": "HEX2DEC",
    "HEX.A.OCT": "HEX2OCT",
    "HIPERVINCULO": "HYPERLINK",
    "HOJA": "SHEET",
    "HOJAS": "SHEETS",
    "HORA": "HOUR",
    "HORANUMERO": "TIMEVALUE",
    "HOY": "TODAY",
    # I
    "ID.REGISTRO": "REGISTER.ID",
    "IGUAL": "EXACT",
    "IM.ABS": "IMABS",
    "IM.ANGULO": "IMARGUMENT",
    "IM.CONJUGADA": "IMCONJUGATE",
    "IM.COS": "IMCOS",
    "IM.COSH": "IMCOSH",
    "IM.CSC": "IMCSC",
    "IM.CSCH": "IMCSCH",
    "IM.DIV": "IMDIV",
    "IM.EXP": "IMEXP",
    "IM.LN": "IMLN",
    "IM.LOG10": "IMLOG10",
    "IM.LOG2": "IMLOG2",
    "IM.POT": "IMPOWER",
    "IM.PRODUCT": "IMPRODUCT",
    "IM.RAIZ2": "IMSQRT",
    "IM.REAL": "IMREAL",
    "IM.SEC": "IMSEC",
    "IM.SECH": "IMSECH",
    "IM.SENO": "IMSIN",
    "IM.SENOH": "IMSINH",
    "IM.SUM": "IMSUM",
    "IM.SUSTR": "IMSUB",
    "IM.TAN": "IMTAN",
    "IMAGINARIO": "IMAGINARY",
    "IMCOT": "IMCOT",
    "IMPORTARDATOSDINAMICOS": "GETPIVOTDATA",
    "INDICE": "INDEX",
    "INDIRECTO": "INDIRECT",
    "INFO": "INFO",
    "INT.ACUM": "ACCRINT",
    "INT.ACUM.V": "ACCRINTM",
    "INT.EFECTIVO": "EFFECT",
    "INT.PAGO.DIR": "ISPMT",
    "INTERSECCION.EJE": "INTERCEPT",
    "INTERVALO.CONFIANZA": "CONFIDENCE",
    "INTERVALO.CONFIANZA.NORM": "CONFIDENCE.NORM",
    "INTERVALO.CONFIANZA.T": "CONFIDENCE.T",
    "INV.BETA": "BETA.INV",
    "INV.BINOM": "BINOM.INV",
    "INV.CHICUAD": "CHISQ.INV",
    "INV.CHICUAD.CD": "CHISQ.INV.RT",
    "INV.F": "F.INV",
    "INV.F.CD": "F.INV.RT",
    "INV.GAMMA": "GAMMA.INV",
    "INV.LOGNORM": "LOGNORM.INV",
    "INV.NORM": "NORM.INV",
    "INV.NORM.ESTAND": "NORM.S.INV",
    "INV.T": "T.INV",
    "INV.T.2C": "T.INV.2T",
    "ISO.NUM.DE.SEMANA": "ISOWEEKNUM",
    "IZQUIERDA": "LEFT",
    "IZQUIERDAB": "LEFTB",
    # J
    "JERARQUIA": "RANK",
    "JERARQUIA.EQV": "RANK.EQ",
    "JERARQUIA.MEDIA": "RANK.AVG",
    # K
    "K.ESIMO.MAYOR": "LARGE",
    "K.ESIMO.MENOR": "SMALL",
    # L
    "LARGO": "LEN",
    "LARGOB": "LENB",
    "LETRA.DE.TES.EQV.A.BONO": "TBILLEQ",
    "LETRA.DE.TES.PRECIO": "TBILLPRICE",
    "LETRA.DE.TES.RENDTO": "TBILLYIELD",
    "LIMPIAR": "CLEAN",
    "LLAMAR": "CALL",
    "LN": "LN",
    "LOG": "LOG",
    "LOG10": "LOG10",
    # M
    "M.C.D": "GCD",
    "M.C.M": "LCM",
    "MAX": "MAX",
    "MAXA": "MAXA",
    "MAYOR.O.IGUAL": "GESTEP",
    "MAYUSC": "UPPER",
    "MDETERM": "MDETERM",
    "MEDIA.ACOTADA": "TRIMMEAN",
    "MEDIA.ARMO": "HARMEAN",
    "MEDIA.GEOM": "GEOMEAN",
    "MEDIANA": "MEDIAN",
    "MES": "MONTH",
    "MIEMBRO.CUBO": "CUBEMEMBER",
    "MIEMBROKPI.CUBO": "CUBEKPIMEMBER",
    "MIEMBRORANGO.CUBO": "CUBERANKEDMEMBER",
    "MIN": "MIN",
    "MINA": "MINA",
    "MINUSC": "LOWER",
    "MINUTO": "MINUTE",
    "MINVERSA": "MINVERSE",
    "MMULT": "MMULT",
    "MODA": "MODE",
    "MODA.UNO": "MODE.SNGL",
    "MODA.VARIOS": "MODE.MULT",
    "MONEDA": "DOLLAR",
    "MONEDA.DEC": "DOLLARDE",
    "MONEDA.FRAC": "DOLLARFR",
    "MULTINOMIAL": "MULTINOMIAL",
    "MULTIPLO.INFERIOR": "FLOOR",
    "MULTIPLO.INFERIOR.EXACTO": "FLOOR.PRECISE",
    "MULTIPLO.INFERIOR.MAT": "FLOOR.MATH",
    "MULTIPLO.SUPERIOR": "CEILING",
    "MULTIPLO.SUPERIOR.EXACTO": "CEILING.PRECISE",
    "MULTIPLO.SUPERIOR.ISO": "ISO.CEILING",
    "MUNIT": "MUNIT",
    # N
    "N": "N",
    "NEGBINOM.DIST": "NEGBINOM.DIST",
    "NEGBINOMDIST": "NEGBINOMDIST",
    "NO": "NOT",
    "NOD": "NA",
    "NOMPROPIO": "PROPER",
    "NORMALIZACION": "STANDARDIZE",
    "NPER": "NPER",
    "NUM.DE.SEMANA": "WEEKNUM",
    "NUMERO.ARABE": "ARABIC",
    "NUMERO.ROMANO": "ROMAN",
    # O
    "O": "OR",
    "OCT.A.BIN": "OCT2BIN",
    "OCT.A.DEC": "OCT2DEC",
    "OCT.A.HEX": "OCT2HEX",
    # P
    "P.DURACION": "PDURATION",
    "PAGO": "PMT",
    "PAGO.INT.ENTRE": "CUMIPMT",
    "PAGO.PRINC.ENTRE": "CUMPRINC",
    "PAGOINT": "IPMT",
    "PAGOPRIN": "PPMT",
    "PEARSON": "PEARSON",
    "PENDIENTE": "SLOPE",
    "PERCENTIL": "PERCENTILE",
    "PERCENTIL.EXC": "PERCENTILE.EXC",
    "PERCENTIL.INC": "PERCENTILE.INC",
    "PERMUTACIONES": "PERMUT",
    "PERMUTACIONES.A": "PERMUTATIONA",
    "PI": "PI",
    "POISSON": "POISSON",
    "POISSON.DIST": "POISSON.DIST",
    "POTENCIA": "POWER",
    "PRECIO": "PRICE",
    "PRECIO.DESCUENTO": "PRICEDISC",
    "PRECIO.PER.IRREGULAR.1": "ODDFPRICE",
    "PRECIO.PER.IRREGULAR.2": "ODDLPRICE",
    "PRECIO.VENCIMIENTO": "PRICEMAT",
    "PROBABILIDAD": "PROB",
    "PRODUCTO": "PRODUCT",
    "PROMEDIO": "AVERAGE",
    "PROMEDIO.SI": "AVERAGEIF",
    "PROMEDIO.SI.CONJUNTO": "AVERAGEIFS",
    "PROMEDIOA": "AVERAGEA",
    "PRONOSTICO": "FORECAST",
    "PROPIEDAD.MIEMBRO.CUBO": "CUBEMEMBERPROPERTY",
    "PRUEBA.CHI": "CHITEST",
    "PRUEBA.CHI.INV": "CHIINV",
    "PRUEBA.CHICUAD": "CHISQ.TEST",
    "PRUEBA.F": "FTEST",
    "PRUEBA.F.N": "F.TEST",
    "PRUEBA.FISHER.INV": "FISHERINV",
    "PRUEBA.T": "T.TEST",
    "PRUEBA.T.N": "TTEST",
    "PRUEBA.Z": "Z.TEST",
    "PRUEBA.Z.N": "ZTEST",
    # R
    "RADIANES": "RADIANS",
    "RAIZ": "SQRT",
    "RAIZ2PI": "SQRTPI",
    "RANGO.PERCENTIL": "PERCENTRANK",
    "RANGO.PERCENTIL.EXC": "PERCENTRANK.EXC",
    "RANGO.PERCENTIL.INC": "PERCENTRANK.INC",
    "RDT": "RRI",
    "RECUENTO.CONJUNTO.CUBO": "CUBESETCOUNT",
    "REDOND.MULT": "MROUND",
    "REDONDEA.IMPAR": "ODD",
    "REDONDEA.PAR": "EVEN",
    "REDONDEAR": "ROUND",
    "REDONDEAR.MAS": "ROUNDUP",
    "REDONDEAR.MENOS": "ROUNDDOWN",
    "REEMPLAZAR": "REPLACE",
    "REEMPLAZARB": "REPLACEB",
    "RENDTO": "YIELD",
    "RENDTO.DESC": "YIELDDISC",
    "RENDTO.PER.IRREGULAR.1": "ODDFYIELD",
    "RENDTO.PER.IRREGULAR.2": "ODDLYIELD",
    "RENDTO.VENCTO": "YIELDMAT",
    "REPETIR": "REPT",
    "RESIDUO": "MOD",
    "RRI": "RRI",
    # S
    "SEC": "SEC",
    "SECH": "SECH",
    "SEGUNDO": "SECOND",
    "SENO": "SIN",
    "SENOH": "SINH",
    "SERVICIO.WEB": "WEBSERVICE",
    "SI": "IF",
    "SI.ERROR": "IFERROR",
    "SI.ND": "IFNA",
    "SIGNO": "SIGN",
    "SLN": "SLN",
    "SQL.REQUEST": "SQL.REQUEST",
    "SUBTOTALES": "SUBTOTAL",
    "SUMA": "SUM",
    "SUMA.CUADRADOS": "SUMSQ",
    "SUMA.SERIES": "SERIESSUM",
    "SUMAPRODUCTO": "SUMPRODUCT",
    "SUMAR.SI": "SUMIF",
    "SUMAR.SI.CONJUNTO": "SUMIFS",
    "SUMAX2MASY2": "SUMX2PY2",
    "SUMAX2MENOSY2": "SUMX2MY2",
    "SUMAXMENOSY2": "SUMXMY2",
    "SUSTITUIR": "SUBSTITUTE",
    "SYD": "SYD",
    # T
    "T": "T",
    "TAN": "TAN",
    "TANH": "TANH",
    "TASA": "RATE",
    "TASA.DESC": "DISC",
    "TASA.INT": "INTRATE",
    "TASA.NOMINAL": "NOMINAL",
    "TENDENCIA": "TREND",
    "TEXTO": "TEXT",
    "TEXTOBAHT": "BAHTTEXT",
    "TIEMPO": "TIME",
    "TIPO": "TYPE",
    "TIPO.DE.ERROR": "ERROR.TYPE",
    "TIR": "IRR",
    "TIR.NO.PER": "XIRR",
    "TIRM": "MIRR",
    "TRANSPONER": "TRANSPOSE",
    "TRUNCAR": "TRUNC",
    # U
    "UNICAR": "UNICHAR",
    "UNICODE": "UNICODE",
    "UNIR.CADENAS": "TEXTJOIN",
    "URLCODIF": "ENCODEURL",
    # V
    "VA": "PV",
    "VALOR": "VALUE",
    "VALOR.CUBO": "CUBEVALUE",
    "VALOR.NUMERO": "NUMBERVALUE",
    "VAR": "VAR",
    "VAR.P": "VAR.P",
    "VAR.S": "VAR.S",
    "VARA": "VARA",
    "VARP": "VARP",
    "VARPA": "VARPA",
    "VERDADERO": "TRUE",
    "VF": "FV",
    "VF.PLAN": "FVSCHEDULE",
    "VNA": "NPV",
    "VNA.NO.PER": "XNPV",
    # X
    "XMLFILTRO": "FILTERXML",
    "XO": "XOR",
    # Y
    "Y": "AND",
    # Dynamic array functions (Excel 365)
    "FILTRAR": "FILTER",
    "ORDENAR": "SORT",
    "ORDENARPOR": "SORTBY",
    "UNICOS": "UNIQUE",
    "SECUENCIA": "SEQUENCE",
    "MATRIZALEAT": "RANDARRAY",
    "LET": "LET",
    "LAMBDA": "LAMBDA",
    "DIVIDIRTEXTO": "TEXTSPLIT",
    "APILARV": "VSTACK",
    "APILARH": "HSTACK",
    "AJUSTARFILAS": "WRAPROWS",
    "AJUSTARCOLS": "WRAPCOLS",
    "TOMAFILAS": "TAKEROWS",
    "TOMACOLS": "TAKECOLS",
    "QUITARFILAS": "DROPROWS",
    "QUITARCOLS": "DROPCOLS",
    "EXPANDIR": "EXPAND",
}

# Build reverse mapping (English to Spanish) for response localization
ENGLISH_TO_SPANISH = {v: k for k, v in SPANISH_TO_ENGLISH.items()}

# ─── Language mappings registry ───────────────────────────────────────────────

TRANSLATIONS = {
    "es": SPANISH_TO_ENGLISH,
    "spanish": SPANISH_TO_ENGLISH,
    "español": SPANISH_TO_ENGLISH,
}

REVERSE_TRANSLATIONS = {
    "es": ENGLISH_TO_SPANISH,
    "spanish": ENGLISH_TO_SPANISH,
    "español": ENGLISH_TO_SPANISH,
}


# ─── Public API ───────────────────────────────────────────────────────────────

def get_english_name(localized_name: str, language: str = "es") -> str:
    """
    Get the English name of an Excel function from its localized name.
    
    Args:
        localized_name: Function name in the local language (e.g., "BUSCARV")
        language: Language code or name (e.g., "es", "spanish", "español")
    
    Returns:
        English function name (e.g., "VLOOKUP"), or original if not found
    """
    lang_key = language.lower()
    if lang_key not in TRANSLATIONS:
        return localized_name.upper()
    
    mapping = TRANSLATIONS[lang_key]
    return mapping.get(localized_name.upper(), localized_name.upper())


def get_localized_name(english_name: str, language: str = "es") -> str:
    """
    Get the localized name of an Excel function from its English name.
    
    Args:
        english_name: Function name in English (e.g., "VLOOKUP")
        language: Target language code (e.g., "es")
    
    Returns:
        Localized function name (e.g., "BUSCARV"), or original if not found
    """
    lang_key = language.lower()
    if lang_key not in REVERSE_TRANSLATIONS:
        return english_name.upper()
    
    mapping = REVERSE_TRANSLATIONS[lang_key]
    return mapping.get(english_name.upper(), english_name.upper())


def normalize_formula(formula: str, language: str = "es") -> str:
    """
    Normalize a formula by replacing localized function names with English equivalents.
    
    Args:
        formula: Excel formula with localized function names
        language: Source language code
    
    Returns:
        Formula with English function names
    
    Example:
        >>> normalize_formula("=SI(BUSCARV(A1,B:C,2,0)>0,SUMA(D:D),0)", "es")
        '=IF(VLOOKUP(A1,B:C,2,0)>0,SUM(D:D),0)'
    """
    if not formula or not formula.startswith("="):
        return formula
    
    lang_key = language.lower()
    if lang_key not in TRANSLATIONS:
        return formula
    
    mapping = TRANSLATIONS[lang_key]
    
    # Pattern to match function names (word followed by opening parenthesis)
    # Handles: SUMA(, SI.ERROR(, BUSCARV(
    def replace_func(match):
        func_name = match.group(1).upper()
        english_name = mapping.get(func_name, func_name)
        return english_name + "("
    
    # Match function names (allowing dots in names like SI.ERROR)
    pattern = r'\b([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ0-9_.]*)\s*\('
    normalized = re.sub(pattern, replace_func, formula, flags=re.IGNORECASE)
    
    return normalized


def detect_language_from_formula(formula: str) -> Optional[str]:
    """
    Attempt to detect the language of a formula based on function names.
    
    Args:
        formula: Excel formula
    
    Returns:
        Language code if detected, None otherwise
    """
    if not formula:
        return None
    
    # Extract potential function names
    pattern = r'\b([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ0-9_.]*)\s*\('
    matches = re.findall(pattern, formula, flags=re.IGNORECASE)
    
    if not matches:
        return None
    
    # Check Spanish indicators
    spanish_indicators = {"SI", "SUMA", "BUSCARV", "BUSCARH", "COINCIDIR", 
                          "INDICE", "PROMEDIO", "CONTAR", "VERDADERO", "FALSO"}
    
    for func in matches:
        if func.upper() in spanish_indicators:
            return "es"
    
    # Check if all functions are English (default)
    english_funcs = {"IF", "SUM", "VLOOKUP", "HLOOKUP", "MATCH", "INDEX",
                     "AVERAGE", "COUNT", "TRUE", "FALSE"}
    
    for func in matches:
        if func.upper() in english_funcs:
            return "en"
    
    return None


# ─── Statistics ───────────────────────────────────────────────────────────────

def get_translation_stats() -> dict:
    """Return statistics about available translations."""
    return {
        "languages": list(TRANSLATIONS.keys()),
        "spanish_functions": len(SPANISH_TO_ENGLISH),
    }


# ─── Module exports ───────────────────────────────────────────────────────────

__all__ = [
    "get_english_name",
    "get_localized_name", 
    "normalize_formula",
    "detect_language_from_formula",
    "get_translation_stats",
    "SPANISH_TO_ENGLISH",
    "ENGLISH_TO_SPANISH",
]
