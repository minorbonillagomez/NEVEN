# -*- coding: utf-8 -*-
"""
skill_loader.py - Carga skills de C:/NEVEN/skills/ para inyectar en system prompts.

Los skills definen METODOLOGIA (como responder), no contenido.
El contenido viene del RAG. La ontologia define validez.

Uso:
    from skill_loader import load_skills_for_agent, build_skill_prompt_section
    
    # Cargar skills para el Profesor de Economia
    skills = load_skills_for_agent("profesor-economia")
    prompt_section = build_skill_prompt_section(skills)
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any

_log = logging.getLogger("neven.skill_loader")

SKILLS_DIR = r"C:\NEVEN\skills"

# Mapeo de agentes a skills que aplican
AGENT_SKILL_MAP = {
    "profesor-economia": ["econometria", "citation-verification", "unslop-academic"],
    "excel-consultant": ["excel-consultant", "statistical-analysis", "unslop-academic"],
    "ai-assistant": ["statistical-analysis", "unslop-academic"],
}

# Skills que siempre se activan (always_active: true en frontmatter)
ALWAYS_ACTIVE_SKILLS = ["citation-verification", "unslop-academic"]


def parse_skill_frontmatter(content: str) -> Dict[str, Any]:
    """Extrae el frontmatter YAML de un SKILL.md.
    
    Formato:
    ---
    name: skill-name
    description: ...
    version: "1.0"
    always_active: true  # opcional
    restricted_to_rag: true  # opcional
    ---
    # Contenido del skill
    """
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        return {}
    
    # Parse YAML simple sin dependencia externa
    fm_text = fm_match.group(1)
    result = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if ':' in line and not line.startswith('#'):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Convertir booleanos
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            result[key] = value
    return result


def load_skill(skill_name: str) -> Optional[Dict[str, Any]]:
    """Carga un skill individual por nombre.
    
    Returns:
        Dict con keys: name, description, content, frontmatter, references
        o None si no existe.
    """
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    skill_file = os.path.join(skill_dir, "SKILL.md")
    
    if not os.path.isfile(skill_file):
        _log.debug(f"Skill no encontrado: {skill_name}")
        return None
    
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        _log.warning(f"Error leyendo skill {skill_name}: {e}")
        return None
    
    frontmatter = parse_skill_frontmatter(content)
    
    # Extraer contenido despues del frontmatter
    body_match = re.search(r'^---\s*\n.*?\n---\s*\n(.*)$', content, re.DOTALL)
    body = body_match.group(1).strip() if body_match else content.strip()
    
    # Cargar referencias si existen
    references = {}
    refs_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(refs_dir):
        for ref_file in os.listdir(refs_dir):
            if ref_file.endswith(".md"):
                ref_path = os.path.join(refs_dir, ref_file)
                try:
                    with open(ref_path, "r", encoding="utf-8") as f:
                        ref_name = ref_file[:-3]  # quitar .md
                        references[ref_name] = f.read()
                except Exception:
                    pass
    
    return {
        "name": frontmatter.get("name", skill_name),
        "description": frontmatter.get("description", ""),
        "version": frontmatter.get("version", "1.0"),
        "always_active": frontmatter.get("always_active", False),
        "restricted_to_rag": frontmatter.get("restricted_to_rag", False),
        "content": body,
        "frontmatter": frontmatter,
        "references": references,
    }


def load_skills_for_agent(agent_id: str) -> List[Dict[str, Any]]:
    """Carga todos los skills aplicables a un agente.
    
    Args:
        agent_id: Identificador del agente (profesor-economia, excel-consultant, ai-assistant)
    
    Returns:
        Lista de skills cargados.
    """
    skill_names = list(AGENT_SKILL_MAP.get(agent_id, []))
    
    # Agregar skills always_active que no esten ya en la lista
    for always_skill in ALWAYS_ACTIVE_SKILLS:
        if always_skill not in skill_names:
            skill_names.append(always_skill)
    
    skills = []
    for name in skill_names:
        skill = load_skill(name)
        if skill:
            skills.append(skill)
            _log.debug(f"Skill cargado para {agent_id}: {name}")
    
    return skills


def build_skill_prompt_section(skills: List[Dict[str, Any]], 
                                include_references: bool = False,
                                max_content_length: int = 3000) -> str:
    """Construye la seccion de skills para inyectar en el system prompt.
    
    Args:
        skills: Lista de skills cargados
        include_references: Si True, incluye el contenido de references/
        max_content_length: Maximo de caracteres por skill
    
    Returns:
        String formateado para incluir en system prompt.
    """
    if not skills:
        return ""
    
    sections = []
    
    for skill in skills:
        # Header del skill
        header = f"## SKILL: {skill['name']}"
        if skill.get('restricted_to_rag'):
            header += " [RESTRINGIDO A RAG]"
        if skill.get('always_active'):
            header += " [SIEMPRE ACTIVO]"
        
        # Contenido principal (truncado si es muy largo)
        content = skill['content']
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n\n[...contenido truncado...]"
        
        skill_section = f"{header}\n\n{content}"
        
        # Referencias opcionales
        if include_references and skill.get('references'):
            refs_parts = []
            for ref_name, ref_content in skill['references'].items():
                # Truncar referencias individuales
                if len(ref_content) > 1000:
                    ref_content = ref_content[:1000] + "\n[...truncado...]"
                refs_parts.append(f"### Referencia: {ref_name}\n{ref_content}")
            
            if refs_parts:
                skill_section += "\n\n" + "\n\n".join(refs_parts)
        
        sections.append(skill_section)
    
    return "\n\n---\n\n".join(sections)


def get_skill_system_prompt(agent_id: str, 
                            include_references: bool = False) -> str:
    """Shortcut para cargar skills y generar prompt section en un paso.
    
    Args:
        agent_id: profesor-economia, excel-consultant, ai-assistant
        include_references: Si incluir contenido de references/
    
    Returns:
        String listo para inyectar en system prompt.
    """
    skills = load_skills_for_agent(agent_id)
    return build_skill_prompt_section(skills, include_references=include_references)


# Para testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Skills para profesor-economia ===")
    skills = load_skills_for_agent("profesor-economia")
    for s in skills:
        print(f"  - {s['name']}: {s['description'][:60]}...")
        print(f"    references: {list(s['references'].keys())}")
    
    print("\n=== Prompt section (truncado) ===")
    prompt = get_skill_system_prompt("profesor-economia", include_references=True)
    print(prompt[:2000])
