# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN v3.0 — Ontology Manager
# ═══════════════════════════════════════════════════════════════════════════════
# Multi-domain ontology system for the NEVEN knowledge graph.
# Supports loading multiple ontologies (Excel, Econometrics, VBA, etc.)
# and querying them by domain or across all domains.
#
# Directory Structure (production):
#   C:\NEVEN\ontology\
#   ├── domains.json          # Registry of available domains
#   ├── excel\
#   │   ├── schema.yaml
#   │   └── graph.jsonl
#   ├── econometrics\
#   │   ├── schema.yaml
#   │   └── graph.jsonl
#   └── vba\
#       ├── schema.yaml
#       └── graph.jsonl
#
# Author: NEVEN Team (Minor Bonilla Gómez)
# ═══════════════════════════════════════════════════════════════════════════════

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from functools import lru_cache

# ─── Configuration ────────────────────────────────────────────────────────────

# Production path for ontologies
ONTOLOGY_ROOT = r"C:\NEVEN\ontology"

# Development fallback (relative to this file)
# startup → ControlPython → NEVEN → project_root → ONTOLOGIA
_DEV_ONTOLOGY_ROOT = None

def _get_dev_root():
    """Calculate development ontology root relative to this file."""
    global _DEV_ONTOLOGY_ROOT
    if _DEV_ONTOLOGY_ROOT is None:
        try:
            this_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(this_dir)))
            _DEV_ONTOLOGY_ROOT = os.path.join(project_root, "ONTOLOGIA")
        except:
            _DEV_ONTOLOGY_ROOT = ""
    return _DEV_ONTOLOGY_ROOT


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class OntologyDomain:
    """Represents a single ontology domain."""
    id: str                          # e.g., "excel", "econometrics"
    name: str                        # Human-readable name
    description: str                 # What this domain covers
    path: str                        # Path to domain folder
    entity_types: List[str] = field(default_factory=list)  # Types in schema
    entity_count: int = 0            # Number of entities loaded
    loaded: bool = False             # Whether graph is loaded
    
    def __post_init__(self):
        self.entity_types = self.entity_types or []


@dataclass  
class Entity:
    """A single entity from an ontology graph."""
    id: str
    type: str
    domain: str
    properties: Dict[str, Any] = field(default_factory=dict)


# ─── Ontology Manager ─────────────────────────────────────────────────────────

class OntologyManager:
    """
    Manages multiple ontology domains for NEVEN.
    
    Usage:
        manager = OntologyManager()
        manager.discover_domains()
        
        # Query specific domain
        funcs = manager.query("excel", type="ExcelFunction")
        
        # Query across all domains
        results = manager.search_all("VLOOKUP")
        
        # Get domain info
        domains = manager.list_domains()
    """
    
    def __init__(self, root_path: str = None):
        """
        Initialize the ontology manager.
        
        Args:
            root_path: Path to ontology root. Defaults to C:\\NEVEN\\ontology
        """
        self.root_path = root_path or ONTOLOGY_ROOT
        self.domains: Dict[str, OntologyDomain] = {}
        self._entities: Dict[str, Dict[str, Entity]] = {}  # domain -> {id: Entity}
        self._type_index: Dict[str, Dict[str, List[str]]] = {}  # domain -> {type: [ids]}
        self._name_index: Dict[str, Dict[str, str]] = {}  # domain -> {name_upper: id}
        
    # ─── Discovery ────────────────────────────────────────────────────────────
    
    def discover_domains(self) -> List[OntologyDomain]:
        """
        Discover available ontology domains from the filesystem.
        
        Looks for:
        1. domains.json registry file (if exists)
        2. Subdirectories containing graph.jsonl
        
        Returns:
            List of discovered domains
        """
        self.domains.clear()
        
        # Try production path first
        if os.path.isdir(self.root_path):
            self._discover_from_path(self.root_path)
        
        # If nothing found, try development path
        if not self.domains:
            dev_root = _get_dev_root()
            if dev_root and os.path.isdir(dev_root):
                self._discover_from_path(dev_root)
        
        return list(self.domains.values())
    
    def _discover_from_path(self, root: str):
        """Discover domains from a specific root path."""
        # Check for domains.json registry
        registry_path = os.path.join(root, "domains.json")
        if os.path.isfile(registry_path):
            self._load_registry(registry_path)
            return
        
        # Otherwise, scan subdirectories
        for item in os.listdir(root):
            item_path = os.path.join(root, item)
            if os.path.isdir(item_path):
                graph_path = os.path.join(item_path, "graph.jsonl")
                # Also check memory/ontology subfolder (legacy structure)
                legacy_graph = os.path.join(item_path, "memory", "ontology", "graph.jsonl")
                
                if os.path.isfile(graph_path):
                    self._register_domain_from_folder(item, item_path)
                elif os.path.isfile(legacy_graph):
                    # Legacy structure: LIBROS EXCEL/memory/ontology/
                    self._register_domain_from_folder(
                        self._normalize_domain_id(item),
                        os.path.join(item_path, "memory", "ontology")
                    )
    
    def _normalize_domain_id(self, folder_name: str) -> str:
        """Convert folder name to domain ID."""
        # "LIBROS EXCEL" -> "excel"
        # "LIBROS ECONOMETRIA" -> "econometrics"
        name = folder_name.lower().replace("libros ", "").replace(" ", "_")
        mapping = {
            "excel": "excel",
            "econometria": "econometrics", 
            "vba": "vba",
            "analisis_de_datos": "data_analysis",
            "estadistica": "statistics",
        }
        return mapping.get(name, name)
    
    def _register_domain_from_folder(self, domain_id: str, path: str):
        """Register a domain discovered from folder structure."""
        schema_path = os.path.join(path, "schema.yaml")
        entity_types = []
        
        # Load schema to get entity types
        if os.path.isfile(schema_path):
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                    if schema and "types" in schema:
                        entity_types = list(schema["types"].keys())
            except:
                pass
        
        # Count entities without fully loading
        entity_count = 0
        graph_path = os.path.join(path, "graph.jsonl")
        if os.path.isfile(graph_path):
            try:
                with open(graph_path, 'r', encoding='utf-8') as f:
                    entity_count = sum(1 for line in f if line.strip())
            except:
                pass
        
        self.domains[domain_id] = OntologyDomain(
            id=domain_id,
            name=self._domain_display_name(domain_id),
            description=self._domain_description(domain_id),
            path=path,
            entity_types=entity_types,
            entity_count=entity_count,
            loaded=False
        )
    
    def _domain_display_name(self, domain_id: str) -> str:
        """Get human-readable name for a domain."""
        names = {
            "excel": "Microsoft Excel",
            "econometrics": "Econometrics & Statistics",
            "vba": "VBA Programming",
            "data_analysis": "Data Analysis",
            "statistics": "Statistics",
        }
        return names.get(domain_id, domain_id.replace("_", " ").title())
    
    def _domain_description(self, domain_id: str) -> str:
        """Get description for a domain."""
        descriptions = {
            "excel": "Excel functions, formulas, shortcuts, patterns, and best practices for financial modeling",
            "econometrics": "Econometric methods, statistical tests, R packages, and causal inference frameworks",
            "vba": "Visual Basic for Applications programming in Excel",
            "data_analysis": "Data analysis techniques and methodologies",
            "statistics": "Statistical concepts, tests, and distributions",
        }
        return descriptions.get(domain_id, f"Knowledge domain: {domain_id}")
    
    def _load_registry(self, path: str):
        """Load domains from a domains.json registry file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            for domain_data in registry.get("domains", []):
                domain_id = domain_data.get("id")
                if not domain_id:
                    continue
                
                domain_path = domain_data.get("path", domain_id)
                if not os.path.isabs(domain_path):
                    domain_path = os.path.join(os.path.dirname(path), domain_path)
                
                self.domains[domain_id] = OntologyDomain(
                    id=domain_id,
                    name=domain_data.get("name", domain_id),
                    description=domain_data.get("description", ""),
                    path=domain_path,
                    entity_types=domain_data.get("entity_types", []),
                    entity_count=domain_data.get("entity_count", 0),
                    loaded=False
                )
        except Exception as e:
            print(f"[OntologyManager] Failed to load registry: {e}")
    
    # ─── Loading ──────────────────────────────────────────────────────────────
    
    def load_domain(self, domain_id: str) -> bool:
        """
        Load a specific domain's graph into memory.
        
        Args:
            domain_id: Domain identifier (e.g., "excel")
            
        Returns:
            True if loaded successfully
        """
        if domain_id not in self.domains:
            return False
        
        domain = self.domains[domain_id]
        if domain.loaded:
            return True
        
        graph_path = os.path.join(domain.path, "graph.jsonl")
        if not os.path.isfile(graph_path):
            return False
        
        # Initialize indexes for this domain
        self._entities[domain_id] = {}
        self._type_index[domain_id] = {}
        self._name_index[domain_id] = {}
        
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry = json.loads(line)
                        if entry.get("op") == "create":
                            entity_data = entry.get("entity", {})
                            entity_id = entity_data.get("id")
                            entity_type = entity_data.get("type")
                            
                            if entity_id and entity_type:
                                entity = Entity(
                                    id=entity_id,
                                    type=entity_type,
                                    domain=domain_id,
                                    properties=entity_data.get("properties", {})
                                )
                                
                                # Store entity
                                self._entities[domain_id][entity_id] = entity
                                
                                # Index by type
                                if entity_type not in self._type_index[domain_id]:
                                    self._type_index[domain_id][entity_type] = []
                                self._type_index[domain_id][entity_type].append(entity_id)
                                
                                # Index by name (if has name property)
                                name = entity.properties.get("name", "")
                                if name:
                                    self._name_index[domain_id][name.upper()] = entity_id
                    except json.JSONDecodeError:
                        continue
            
            domain.loaded = True
            domain.entity_count = len(self._entities[domain_id])
            return True
            
        except Exception as e:
            print(f"[OntologyManager] Failed to load {domain_id}: {e}")
            return False
    
    def load_all(self) -> int:
        """Load all discovered domains. Returns count of loaded domains."""
        loaded = 0
        for domain_id in self.domains:
            if self.load_domain(domain_id):
                loaded += 1
        return loaded
    
    def ensure_loaded(self, domain_id: str) -> bool:
        """Ensure a domain is loaded, loading it if necessary."""
        if domain_id not in self.domains:
            self.discover_domains()
        return self.load_domain(domain_id)
    
    # ─── Querying ─────────────────────────────────────────────────────────────
    
    def query(self, domain_id: str, 
              type: str = None, 
              name: str = None,
              limit: int = 100) -> List[Entity]:
        """
        Query entities from a specific domain.
        
        Args:
            domain_id: Domain to query
            type: Filter by entity type (e.g., "ExcelFunction")
            name: Filter by name (case-insensitive)
            limit: Maximum results to return
            
        Returns:
            List of matching entities
        """
        if not self.ensure_loaded(domain_id):
            return []
        
        entities = self._entities.get(domain_id, {})
        
        # If querying by name
        if name:
            entity_id = self._name_index.get(domain_id, {}).get(name.upper())
            if entity_id and entity_id in entities:
                entity = entities[entity_id]
                if type is None or entity.type == type:
                    return [entity]
            return []
        
        # If querying by type
        if type:
            entity_ids = self._type_index.get(domain_id, {}).get(type, [])
            return [entities[eid] for eid in entity_ids[:limit] if eid in entities]
        
        # Return all (limited)
        return list(entities.values())[:limit]
    
    def get_by_name(self, domain_id: str, name: str) -> Optional[Entity]:
        """Get a single entity by name from a domain."""
        results = self.query(domain_id, name=name)
        return results[0] if results else None
    
    def get_by_id(self, domain_id: str, entity_id: str) -> Optional[Entity]:
        """Get a single entity by ID from a domain."""
        if not self.ensure_loaded(domain_id):
            return None
        return self._entities.get(domain_id, {}).get(entity_id)
    
    def search_all(self, query: str, 
                   types: List[str] = None,
                   domains: List[str] = None,
                   limit: int = 50) -> List[Entity]:
        """
        Search across all domains (or specified domains).
        
        Args:
            query: Search term (matches name, description)
            types: Filter by entity types
            domains: Limit to specific domains (None = all)
            limit: Maximum results
            
        Returns:
            List of matching entities across domains
        """
        results = []
        query_upper = query.upper()
        
        target_domains = domains or list(self.domains.keys())
        
        for domain_id in target_domains:
            if not self.ensure_loaded(domain_id):
                continue
            
            for entity in self._entities.get(domain_id, {}).values():
                if types and entity.type not in types:
                    continue
                
                # Search in name and description
                name = entity.properties.get("name", "").upper()
                desc = entity.properties.get("description", "").upper()
                definition = entity.properties.get("definition", "").upper()
                
                if query_upper in name or query_upper in desc or query_upper in definition:
                    results.append(entity)
                    if len(results) >= limit:
                        return results
        
        return results
    
    # ─── Info ─────────────────────────────────────────────────────────────────
    
    def list_domains(self) -> List[Dict[str, Any]]:
        """Get list of available domains with metadata."""
        if not self.domains:
            self.discover_domains()
        
        return [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "entity_types": d.entity_types,
                "entity_count": d.entity_count,
                "loaded": d.loaded,
            }
            for d in self.domains.values()
        ]
    
    def get_domain_stats(self, domain_id: str) -> Dict[str, Any]:
        """Get statistics for a loaded domain."""
        if not self.ensure_loaded(domain_id):
            return {"error": f"Domain '{domain_id}' not found"}
        
        domain = self.domains[domain_id]
        type_counts = {
            t: len(ids) 
            for t, ids in self._type_index.get(domain_id, {}).items()
        }
        
        return {
            "id": domain.id,
            "name": domain.name,
            "entity_count": domain.entity_count,
            "type_counts": type_counts,
        }


# ─── Singleton instance ───────────────────────────────────────────────────────

_manager_instance: Optional[OntologyManager] = None

def get_manager() -> OntologyManager:
    """Get the singleton OntologyManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = OntologyManager()
        _manager_instance.discover_domains()
    return _manager_instance


# ─── Convenience functions ────────────────────────────────────────────────────

def get_excel_function(name: str) -> Optional[Dict[str, Any]]:
    """
    Quick lookup for an Excel function by name.
    
    Returns dict with category, description, syntax, best_practices, common_errors.
    """
    manager = get_manager()
    entity = manager.get_by_name("excel", name)
    
    if entity and entity.type == "ExcelFunction":
        return {
            "id": entity.id,
            "name": entity.properties.get("name"),
            "category": entity.properties.get("category", ""),
            "description": entity.properties.get("description", ""),
            "syntax": entity.properties.get("syntax", ""),
            "best_practices": entity.properties.get("best_practices", []),
            "common_errors": entity.properties.get("common_errors", []),
        }
    return None


def get_econometric_method(name: str) -> Optional[Dict[str, Any]]:
    """Quick lookup for an econometric method by name."""
    manager = get_manager()
    entity = manager.get_by_name("econometrics", name)
    
    if entity:
        return {
            "id": entity.id,
            "type": entity.type,
            "name": entity.properties.get("name"),
            "description": entity.properties.get("description", entity.properties.get("definition", "")),
            "reference": entity.properties.get("reference", {}),
        }
    return None


def search_knowledge(query: str, domain: str = None) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph for a term.
    
    Args:
        query: Search term
        domain: Optional domain to limit search (None = all)
        
    Returns:
        List of matching entities as dicts
    """
    manager = get_manager()
    domains = [domain] if domain else None
    entities = manager.search_all(query, domains=domains)
    
    return [
        {
            "id": e.id,
            "type": e.type,
            "domain": e.domain,
            "name": e.properties.get("name", ""),
            "description": e.properties.get("description", e.properties.get("definition", "")),
        }
        for e in entities
    ]


# ─── Export ───────────────────────────────────────────────────────────────────

__all__ = [
    "OntologyManager",
    "OntologyDomain", 
    "Entity",
    "get_manager",
    "get_excel_function",
    "get_econometric_method",
    "search_knowledge",
]
