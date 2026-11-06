"""
NEVEN Studio - Markdown to SSML Converter
Convierte texto Markdown a SSML con pausas y énfasis semánticos.

Los elementos Markdown tienen significado para la narración:
- # Título principal → Pausa larga (1.5s) antes y después
- ## Título secundario → Pausa media (1s) antes y después  
- ### Subtítulo → Pausa normal (0.5s) antes y después
- #### Elemento destacado → Énfasis con incremento de volumen/pitch
- **negrita** → Énfasis fuerte
- *cursiva* → Énfasis suave
- - lista → Pausa breve entre items
- > cita → Tono diferente (más bajo)
- --- → Pausa larga de sección (2s)

@version 1.0.0
@date 2026-08-19
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class SSMLConfig:
    """Configuración de pausas y énfasis para SSML"""
    # Pausas para headers (en milisegundos)
    h1_pause_before: int = 1500  # Pausa larga antes de título principal
    h1_pause_after: int = 1000   # Pausa después
    h2_pause_before: int = 1000  # Pausa media antes de título secundario
    h2_pause_after: int = 750
    h3_pause_before: int = 500   # Pausa normal antes de subtítulo
    h3_pause_after: int = 400
    h4_pause_before: int = 300   # Pausa breve antes de elemento destacado
    h4_pause_after: int = 200
    
    # Énfasis para headers
    h1_emphasis: str = "strong"     # Énfasis fuerte para h1
    h2_emphasis: str = "moderate"   # Énfasis moderado para h2
    h3_emphasis: str = "none"       # Sin énfasis extra para h3
    h4_emphasis: str = "strong"     # Énfasis fuerte + pitch para h4 (destacar)
    h4_pitch: str = "+10%"          # Incremento de pitch para h4
    h4_rate: str = "-5%"            # Ligeramente más lento para énfasis
    
    # Otras pausas
    paragraph_pause: int = 600      # Pausa entre párrafos
    list_item_pause: int = 300      # Pausa entre items de lista
    horizontal_rule_pause: int = 2000  # Pausa larga para separadores ---
    blockquote_pitch: str = "-5%"   # Tono más bajo para citas
    
    # Énfasis de formato inline
    bold_emphasis: str = "strong"
    italic_emphasis: str = "moderate"


def escape_ssml(text: str) -> str:
    """Escapa caracteres especiales para SSML válido"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text


def markdown_to_ssml(markdown_text: str, voice_id: str = "es-MX-DaliaNeural", 
                     config: Optional[SSMLConfig] = None) -> str:
    """
    Convierte texto Markdown a SSML con pausas y énfasis semánticos.
    
    Args:
        markdown_text: Texto en formato Markdown
        voice_id: ID de la voz Edge TTS a usar
        config: Configuración de pausas/énfasis (usa defaults si None)
    
    Returns:
        SSML válido para síntesis de voz
    """
    if config is None:
        config = SSMLConfig()
    
    lines = markdown_text.split('\n')
    ssml_parts = []
    
    # Header SSML
    ssml_parts.append(f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="es-MX">')
    ssml_parts.append(f'<voice name="{voice_id}">')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Línea vacía → pausa de párrafo
        if not stripped:
            i += 1
            continue
        
        # Separador horizontal (---, ***, ___) → pausa larga de sección
        if re.match(r'^[-*_]{3,}$', stripped):
            ssml_parts.append(f'<break time="{config.horizontal_rule_pause}ms"/>')
            i += 1
            continue
        
        # Headers (# ## ### ####)
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            header_text = escape_ssml(header_match.group(2))
            
            ssml_parts.append(_process_header(header_text, level, config))
            i += 1
            continue
        
        # Blockquote (>)
        if stripped.startswith('>'):
            quote_text = escape_ssml(stripped.lstrip('> '))
            ssml_parts.append(
                f'<prosody pitch="{config.blockquote_pitch}">'
                f'<break time="300ms"/>{quote_text}<break time="300ms"/>'
                f'</prosody>'
            )
            i += 1
            continue
        
        # Lista (- * + o número.)
        list_match = re.match(r'^[-*+]|\d+\.\s+', stripped)
        if list_match:
            list_text = re.sub(r'^[-*+]\s*|\d+\.\s*', '', stripped)
            list_text = _process_inline_formatting(escape_ssml(list_text), config)
            ssml_parts.append(
                f'<break time="{config.list_item_pause}ms"/>'
                f'{list_text}'
            )
            i += 1
            continue
        
        # Párrafo normal
        paragraph_text = _process_inline_formatting(escape_ssml(stripped), config)
        ssml_parts.append(f'{paragraph_text}<break time="{config.paragraph_pause}ms"/>')
        i += 1
    
    # Footer SSML
    ssml_parts.append('</voice>')
    ssml_parts.append('</speak>')
    
    return '\n'.join(ssml_parts)


def _process_header(text: str, level: int, config: SSMLConfig) -> str:
    """Genera SSML para un header según su nivel"""
    
    if level == 1:
        # H1: Título principal - pausa larga + énfasis fuerte
        return (
            f'<break time="{config.h1_pause_before}ms"/>'
            f'<emphasis level="{config.h1_emphasis}">{text}</emphasis>'
            f'<break time="{config.h1_pause_after}ms"/>'
        )
    
    elif level == 2:
        # H2: Título secundario - pausa media + énfasis moderado
        return (
            f'<break time="{config.h2_pause_before}ms"/>'
            f'<emphasis level="{config.h2_emphasis}">{text}</emphasis>'
            f'<break time="{config.h2_pause_after}ms"/>'
        )
    
    elif level == 3:
        # H3: Subtítulo - pausa normal, sin énfasis extra
        return (
            f'<break time="{config.h3_pause_before}ms"/>'
            f'{text}'
            f'<break time="{config.h3_pause_after}ms"/>'
        )
    
    elif level == 4:
        # H4: Elemento destacado - énfasis fuerte + pitch elevado
        return (
            f'<break time="{config.h4_pause_before}ms"/>'
            f'<prosody pitch="{config.h4_pitch}" rate="{config.h4_rate}">'
            f'<emphasis level="{config.h4_emphasis}">{text}</emphasis>'
            f'</prosody>'
            f'<break time="{config.h4_pause_after}ms"/>'
        )
    
    else:
        # H5, H6: igual que H4 pero sin pitch
        return (
            f'<break time="200ms"/>'
            f'<emphasis level="moderate">{text}</emphasis>'
            f'<break time="200ms"/>'
        )


def _process_inline_formatting(text: str, config: SSMLConfig) -> str:
    """Procesa formato inline (negrita, cursiva) a SSML"""
    
    # **negrita** → énfasis fuerte
    text = re.sub(
        r'\*\*(.+?)\*\*',
        f'<emphasis level="{config.bold_emphasis}">\\1</emphasis>',
        text
    )
    
    # __negrita alternativa__ → énfasis fuerte
    text = re.sub(
        r'__(.+?)__',
        f'<emphasis level="{config.bold_emphasis}">\\1</emphasis>',
        text
    )
    
    # *cursiva* → énfasis moderado
    text = re.sub(
        r'(?<!\*)\*([^*]+)\*(?!\*)',
        f'<emphasis level="{config.italic_emphasis}">\\1</emphasis>',
        text
    )
    
    # _cursiva alternativa_ → énfasis moderado
    text = re.sub(
        r'(?<!_)_([^_]+)_(?!_)',
        f'<emphasis level="{config.italic_emphasis}">\\1</emphasis>',
        text
    )
    
    # `código` → deletrear más lento
    text = re.sub(
        r'`([^`]+)`',
        r'<prosody rate="-10%">\1</prosody>',
        text
    )
    
    return text


def markdown_to_plain_with_pauses(markdown_text: str, config: Optional[SSMLConfig] = None) -> str:
    """
    Convierte Markdown a texto plano con pausas usando puntuación.
    Útil para TTS que no soportan SSML (como Windows SAPI básico).
    
    Usa puntos y elipsis para indicar pausas:
    - # → ... (pausa larga)
    - ## → .. (pausa media)
    - ### → . (pausa normal)
    - #### → : (indicador de énfasis)
    """
    if config is None:
        config = SSMLConfig()
    
    lines = markdown_text.split('\n')
    result_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            continue
        
        # Separador horizontal
        if re.match(r'^[-*_]{3,}$', stripped):
            result_lines.append('\n...\n')
            continue
        
        # Headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            header_text = header_match.group(2)
            
            if level == 1:
                result_lines.append(f'\n... {header_text}. ...\n')
            elif level == 2:
                result_lines.append(f'\n.. {header_text}. ..\n')
            elif level == 3:
                result_lines.append(f'\n. {header_text}.\n')
            elif level == 4:
                result_lines.append(f'\n¡{header_text}!\n')  # Énfasis con exclamación
            else:
                result_lines.append(f'\n{header_text}.\n')
            continue
        
        # Blockquote
        if stripped.startswith('>'):
            quote_text = stripped.lstrip('> ')
            result_lines.append(f'"{quote_text}"')
            continue
        
        # Lista
        list_match = re.match(r'^[-*+]|\d+\.\s+', stripped)
        if list_match:
            list_text = re.sub(r'^[-*+]\s*|\d+\.\s*', '', stripped)
            result_lines.append(f'. {list_text}')
            continue
        
        # Párrafo normal - eliminar formato Markdown inline
        plain_text = stripped
        plain_text = re.sub(r'\*\*(.+?)\*\*', r'\1', plain_text)  # negrita
        plain_text = re.sub(r'__(.+?)__', r'\1', plain_text)
        plain_text = re.sub(r'\*(.+?)\*', r'\1', plain_text)       # cursiva
        plain_text = re.sub(r'_(.+?)_', r'\1', plain_text)
        plain_text = re.sub(r'`(.+?)`', r'\1', plain_text)         # código
        plain_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain_text)  # links
        
        result_lines.append(plain_text)
    
    return '\n'.join(result_lines)


# Exportar configuración por defecto
DEFAULT_SSML_CONFIG = SSMLConfig()


if __name__ == "__main__":
    # Test
    test_md = """
# Capítulo 1: Introducción

Este es el primer párrafo del capítulo. Contiene **texto importante** y *texto enfatizado*.

## Sección 1.1: Contexto

El contexto de esta investigación es muy relevante.

### Subsección: Antecedentes

Algunos antecedentes importantes:

- Primer punto de la lista
- Segundo punto
- Tercer punto

#### Nota importante

Este es un elemento que debe destacarse con más énfasis.

---

## Sección 1.2: Objetivos

> Esta es una cita textual de otro autor.

Los objetivos son claros y medibles.
"""
    
    print("=" * 60)
    print("NEVEN Studio - Markdown to SSML Converter Test")
    print("=" * 60)
    
    ssml = markdown_to_ssml(test_md, "es-MX-DaliaNeural")
    print("\n📝 SSML generado:")
    print(ssml)
    
    print("\n" + "=" * 60)
    print("📝 Texto plano con pausas:")
    plain = markdown_to_plain_with_pauses(test_md)
    print(plain)
