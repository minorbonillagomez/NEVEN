# -*- coding: utf-8 -*-
"""
test_skill_loader.py - Tests unitarios para skill_loader.py

Ejecutar con:
    python -m pytest tests/test_skill_loader.py -v
    
O directamente:
    python tests/test_skill_loader.py
"""

import os
import sys
import tempfile
import shutil
import unittest

# Agregar path de startup para importar skill_loader
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "startup"))

# También probar con el path de producción si existe
PROD_STARTUP = r"C:\NEVEN\startup"
if os.path.isdir(PROD_STARTUP) and PROD_STARTUP not in sys.path:
    sys.path.insert(0, PROD_STARTUP)

from skill_loader import (
    parse_skill_frontmatter,
    load_skill,
    load_skills_for_agent,
    build_skill_prompt_section,
    get_skill_system_prompt,
    AGENT_SKILL_MAP,
    ALWAYS_ACTIVE_SKILLS,
)


class TestParseFrontmatter(unittest.TestCase):
    """Tests para parse_skill_frontmatter()"""
    
    def test_basic_frontmatter(self):
        """Parsea frontmatter YAML básico"""
        content = """---
name: test-skill
description: A test skill
version: "1.0"
---
# Contenido
"""
        result = parse_skill_frontmatter(content)
        self.assertEqual(result["name"], "test-skill")
        self.assertEqual(result["description"], "A test skill")
        self.assertEqual(result["version"], "1.0")
    
    def test_boolean_values(self):
        """Convierte strings true/false a booleanos"""
        content = """---
always_active: true
restricted_to_rag: false
---
Body
"""
        result = parse_skill_frontmatter(content)
        self.assertIs(result["always_active"], True)
        self.assertIs(result["restricted_to_rag"], False)
    
    def test_quoted_values(self):
        """Maneja valores con comillas simples y dobles"""
        content = """---
name: "quoted-double"
version: '1.0'
---
"""
        result = parse_skill_frontmatter(content)
        self.assertEqual(result["name"], "quoted-double")
        self.assertEqual(result["version"], "1.0")
    
    def test_no_frontmatter(self):
        """Retorna dict vacío si no hay frontmatter"""
        content = "# Just content\nNo frontmatter here"
        result = parse_skill_frontmatter(content)
        self.assertEqual(result, {})
    
    def test_comments_ignored(self):
        """Ignora líneas de comentario en frontmatter"""
        content = """---
name: skill
# Este es un comentario
description: desc
---
"""
        result = parse_skill_frontmatter(content)
        self.assertEqual(result["name"], "skill")
        self.assertEqual(result["description"], "desc")
        self.assertNotIn("#", str(result.keys()))


class TestLoadSkill(unittest.TestCase):
    """Tests para load_skill()"""
    
    @classmethod
    def setUpClass(cls):
        """Crea directorio temporal con skills de prueba"""
        cls.temp_dir = tempfile.mkdtemp(prefix="neven_skills_test_")
        
        # Crear skill de prueba: test-skill
        skill_dir = os.path.join(cls.temp_dir, "test-skill")
        os.makedirs(skill_dir)
        
        skill_content = """---
name: test-skill
description: Skill de prueba para tests unitarios
version: "1.0"
always_active: false
---

# Test Skill

Este es un skill de prueba.

## Sección 1

Contenido de la sección.
"""
        with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(skill_content)
        
        # Crear referencias
        refs_dir = os.path.join(skill_dir, "references")
        os.makedirs(refs_dir)
        
        with open(os.path.join(refs_dir, "ref1.md"), "w", encoding="utf-8") as f:
            f.write("# Referencia 1\n\nContenido de referencia.")
        
        with open(os.path.join(refs_dir, "ref2.md"), "w", encoding="utf-8") as f:
            f.write("# Referencia 2\n\nOtra referencia.")
        
        # Guardar el SKILLS_DIR original y cambiarlo
        import skill_loader
        cls.original_skills_dir = skill_loader.SKILLS_DIR
        skill_loader.SKILLS_DIR = cls.temp_dir
    
    @classmethod
    def tearDownClass(cls):
        """Limpia directorio temporal"""
        import skill_loader
        skill_loader.SKILLS_DIR = cls.original_skills_dir
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_load_existing_skill(self):
        """Carga un skill que existe"""
        skill = load_skill("test-skill")
        self.assertIsNotNone(skill)
        self.assertEqual(skill["name"], "test-skill")
        self.assertEqual(skill["description"], "Skill de prueba para tests unitarios")
        self.assertIn("Test Skill", skill["content"])
    
    def test_load_nonexistent_skill(self):
        """Retorna None para skill inexistente"""
        skill = load_skill("nonexistent-skill")
        self.assertIsNone(skill)
    
    def test_load_skill_references(self):
        """Carga referencias del skill"""
        skill = load_skill("test-skill")
        self.assertIn("ref1", skill["references"])
        self.assertIn("ref2", skill["references"])
        self.assertIn("Referencia 1", skill["references"]["ref1"])
    
    def test_skill_frontmatter_preserved(self):
        """Preserva frontmatter completo"""
        skill = load_skill("test-skill")
        self.assertIn("frontmatter", skill)
        self.assertEqual(skill["frontmatter"]["version"], "1.0")


class TestLoadSkillsForAgent(unittest.TestCase):
    """Tests para load_skills_for_agent()"""
    
    def test_agent_skill_map_defined(self):
        """Verifica que los agentes principales estén mapeados"""
        self.assertIn("profesor-economia", AGENT_SKILL_MAP)
        self.assertIn("excel-consultant", AGENT_SKILL_MAP)
        self.assertIn("ai-assistant", AGENT_SKILL_MAP)
    
    def test_always_active_skills_defined(self):
        """Verifica skills siempre activos"""
        self.assertIn("citation-verification", ALWAYS_ACTIVE_SKILLS)
        self.assertIn("unslop-academic", ALWAYS_ACTIVE_SKILLS)
    
    def test_unknown_agent_gets_always_active(self):
        """Agente desconocido solo recibe skills always_active"""
        # No usamos el temp_dir aquí, usamos producción si existe
        import skill_loader
        original_dir = skill_loader.SKILLS_DIR
        
        # Si producción existe, probar ahí
        if os.path.isdir(r"C:\NEVEN\skills"):
            skill_loader.SKILLS_DIR = r"C:\NEVEN\skills"
            skills = load_skills_for_agent("unknown-agent")
            skill_loader.SKILLS_DIR = original_dir
            
            # Debería tener al menos los always_active
            skill_names = [s["name"] for s in skills]
            for always_skill in ALWAYS_ACTIVE_SKILLS:
                # Si el skill existe, debería estar cargado
                if os.path.isdir(os.path.join(r"C:\NEVEN\skills", always_skill)):
                    self.assertIn(always_skill, skill_names)


class TestBuildSkillPromptSection(unittest.TestCase):
    """Tests para build_skill_prompt_section()"""
    
    def test_empty_skills(self):
        """Lista vacía retorna string vacío"""
        result = build_skill_prompt_section([])
        self.assertEqual(result, "")
    
    def test_basic_format(self):
        """Genera formato correcto con header y contenido"""
        skills = [{
            "name": "test-skill",
            "content": "Contenido del skill",
            "always_active": False,
            "restricted_to_rag": False,
            "references": {},
        }]
        result = build_skill_prompt_section(skills)
        self.assertIn("## SKILL: test-skill", result)
        self.assertIn("Contenido del skill", result)
    
    def test_always_active_tag(self):
        """Agrega tag [SIEMPRE ACTIVO] cuando aplica"""
        skills = [{
            "name": "always-on",
            "content": "Content",
            "always_active": True,
            "restricted_to_rag": False,
            "references": {},
        }]
        result = build_skill_prompt_section(skills)
        self.assertIn("[SIEMPRE ACTIVO]", result)
    
    def test_restricted_tag(self):
        """Agrega tag [RESTRINGIDO A RAG] cuando aplica"""
        skills = [{
            "name": "rag-only",
            "content": "Content",
            "always_active": False,
            "restricted_to_rag": True,
            "references": {},
        }]
        result = build_skill_prompt_section(skills)
        self.assertIn("[RESTRINGIDO A RAG]", result)
    
    def test_content_truncation(self):
        """Trunca contenido que excede max_content_length"""
        long_content = "A" * 5000
        skills = [{
            "name": "long-skill",
            "content": long_content,
            "always_active": False,
            "restricted_to_rag": False,
            "references": {},
        }]
        result = build_skill_prompt_section(skills, max_content_length=100)
        self.assertIn("[...contenido truncado...]", result)
        self.assertLess(len(result), 5000)
    
    def test_multiple_skills_separator(self):
        """Separa múltiples skills con ---"""
        skills = [
            {"name": "skill1", "content": "C1", "always_active": False, 
             "restricted_to_rag": False, "references": {}},
            {"name": "skill2", "content": "C2", "always_active": False,
             "restricted_to_rag": False, "references": {}},
        ]
        result = build_skill_prompt_section(skills)
        self.assertIn("---", result)
        self.assertIn("## SKILL: skill1", result)
        self.assertIn("## SKILL: skill2", result)
    
    def test_include_references(self):
        """Incluye referencias cuando include_references=True"""
        skills = [{
            "name": "with-refs",
            "content": "Main content",
            "always_active": False,
            "restricted_to_rag": False,
            "references": {
                "important-ref": "Reference content here"
            },
        }]
        result = build_skill_prompt_section(skills, include_references=True)
        self.assertIn("### Referencia: important-ref", result)
        self.assertIn("Reference content here", result)
    
    def test_exclude_references_by_default(self):
        """No incluye referencias por defecto"""
        skills = [{
            "name": "with-refs",
            "content": "Main content",
            "always_active": False,
            "restricted_to_rag": False,
            "references": {
                "ref": "Should not appear"
            },
        }]
        result = build_skill_prompt_section(skills, include_references=False)
        self.assertNotIn("Should not appear", result)


class TestGetSkillSystemPrompt(unittest.TestCase):
    """Tests para get_skill_system_prompt() - integración"""
    
    def test_returns_string(self):
        """Siempre retorna string (puede ser vacío)"""
        result = get_skill_system_prompt("unknown-agent")
        self.assertIsInstance(result, str)
    
    def test_production_skills_if_available(self):
        """Carga skills de producción si el directorio existe"""
        import skill_loader
        
        if os.path.isdir(r"C:\NEVEN\skills"):
            original_dir = skill_loader.SKILLS_DIR
            skill_loader.SKILLS_DIR = r"C:\NEVEN\skills"
            
            result = get_skill_system_prompt("profesor-economia")
            skill_loader.SKILLS_DIR = original_dir
            
            # Debería tener contenido si los skills existen
            self.assertGreater(len(result), 100)
            self.assertIn("SKILL:", result)


class TestAgentMappingCorrectness(unittest.TestCase):
    """Tests para verificar que los mapeos de agentes son correctos"""
    
    def test_profesor_economia_has_econometria(self):
        """Profesor de Economía debe tener skill de econometría"""
        self.assertIn("econometria", AGENT_SKILL_MAP["profesor-economia"])
    
    def test_excel_consultant_has_excel(self):
        """Excel Consultant debe tener skill de excel"""
        self.assertIn("excel-consultant", AGENT_SKILL_MAP["excel-consultant"])
    
    def test_excel_consultant_has_statistical(self):
        """Excel Consultant debe tener skill de estadística"""
        self.assertIn("statistical-analysis", AGENT_SKILL_MAP["excel-consultant"])
    
    def test_all_agents_have_unslop(self):
        """Todos los agentes deben tener unslop-academic (via always_active)"""
        self.assertIn("unslop-academic", ALWAYS_ACTIVE_SKILLS)


if __name__ == "__main__":
    # Ejecutar tests con verbosidad
    unittest.main(verbosity=2)
