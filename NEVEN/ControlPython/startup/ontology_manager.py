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
        
        result = []
        for d in self.domains.values():
            # Count unique books for this domain
            book_count = 0
            if self.ensure_loaded(d.id):
                books = set()
                for entity in self._entities.get(d.id, {}).values():
                    source = entity.properties.get("source_book")
                    if not source:
                        ref = entity.properties.get("reference", {})
                        source = ref.get("book") if isinstance(ref, dict) else None
                    if source:
                        books.add(source)
                book_count = len(books)
            
            result.append({
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "entity_types": d.entity_types,
                "entity_count": d.entity_count,
                "book_count": book_count,
                "loaded": d.loaded,
            })
        
        return result
    
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
    
    def create_domain(self, domain_id: str, display_name: str = None, description: str = None) -> Dict[str, Any]:
        """
        Create a new ontology domain with empty graph.
        
        Creates:
        - Production: C:\\NEVEN\\ontology\\{domain_id}\\
        - Development: ONTOLOGIA\\LIBROS {DISPLAY_NAME}\\memory\\ontology\\
        - Files: graph.jsonl (empty), schema.yaml (basic template)
        
        Args:
            domain_id: Snake_case identifier (e.g., 'machine_learning')
            display_name: Human-readable name (defaults to title case of id)
            description: Domain description
            
        Returns:
            dict with status and domain info
        """
        # Validate domain_id format
        if not domain_id or not domain_id[0].isalpha():
            return {"status": "error", "error": "Domain ID must start with a letter"}
        if not all(c.isalnum() or c == '_' for c in domain_id):
            return {"status": "error", "error": "Domain ID must be alphanumeric with underscores only"}
        
        # Check if already exists
        if domain_id in self.domains:
            return {"status": "error", "error": f"Domain '{domain_id}' already exists"}
        
        # Generate display name if not provided
        if not display_name:
            display_name = domain_id.replace('_', ' ').title()
        
        if not description:
            description = f"Knowledge domain: {display_name}"
        
        # Create production directory structure
        prod_path = os.path.join(ONTOLOGY_ROOT, domain_id)
        os.makedirs(prod_path, exist_ok=True)
        
        # Create graph.jsonl (empty)
        graph_path = os.path.join(prod_path, "graph.jsonl")
        if not os.path.exists(graph_path):
            with open(graph_path, 'w', encoding='utf-8') as f:
                pass  # Empty file
        
        # Create schema.yaml (basic template)
        schema_path = os.path.join(prod_path, "schema.yaml")
        if not os.path.exists(schema_path):
            schema_content = f"""# Ontology schema for {display_name}
# Auto-generated by NEVEN

domain:
  id: {domain_id}
  name: {display_name}
  description: {description}

types:
  Concept:
    description: General concept or term
    properties:
      name: string
      description: string
      source_book: string
  
  Method:
    description: Technique or methodology
    properties:
      name: string
      description: string
      steps: list
      source_book: string
  
  BestPractice:
    description: Recommended practice or pattern
    properties:
      name: string
      description: string
      rationale: string
      source_book: string

relations:
  - type: RELATED_TO
    description: General relationship
  - type: DEPENDS_ON
    description: Dependency relationship
  - type: APPLIES_TO
    description: Application relationship
"""
            with open(schema_path, 'w', encoding='utf-8') as f:
                f.write(schema_content)
        
        # Create development directory structure (ONTOLOGIA/LIBROS X/)
        dev_root = _get_dev_root()
        if dev_root and os.path.isdir(dev_root):
            dev_books_folder = os.path.join(dev_root, f"LIBROS {display_name.upper()}")
            dev_ontology_path = os.path.join(dev_books_folder, "memory", "ontology")
            os.makedirs(dev_ontology_path, exist_ok=True)
            
            # Create symlink or copy schema to dev
            dev_schema = os.path.join(dev_ontology_path, "schema.yaml")
            dev_graph = os.path.join(dev_ontology_path, "graph.jsonl")
            
            if not os.path.exists(dev_schema):
                with open(dev_schema, 'w', encoding='utf-8') as f:
                    f.write(open(schema_path, 'r', encoding='utf-8').read())
            
            if not os.path.exists(dev_graph):
                with open(dev_graph, 'w', encoding='utf-8') as f:
                    pass
        
        # Update domains.json registry
        registry_path = os.path.join(ONTOLOGY_ROOT, "domains.json")
        if os.path.isfile(registry_path):
            try:
                with open(registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                
                # Add new domain
                new_entry = {
                    "id": domain_id,
                    "name": display_name,
                    "description": description,
                    "path": domain_id,
                    "entity_types": ["Concept", "Method", "BestPractice"],
                    "source_books": []
                }
                
                # Check if not already in registry
                existing_ids = [d.get("id") for d in registry.get("domains", [])]
                if domain_id not in existing_ids:
                    registry["domains"].append(new_entry)
                    registry["last_updated"] = __import__('datetime').datetime.now().strftime("%Y-%m-%d")
                    
                    with open(registry_path, 'w', encoding='utf-8') as f:
                        json.dump(registry, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Could not update domains.json: {e}")
        
        # Register in memory
        self.domains[domain_id] = OntologyDomain(
            id=domain_id,
            name=display_name,
            description=description,
            path=prod_path,
            entity_types=["Concept", "Method", "BestPractice"],
            entity_count=0,
            loaded=False
        )
        
        return {
            "status": "ok",
            "domain": {
                "id": domain_id,
                "name": display_name,
                "path": prod_path
            }
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


# ─── Book Processing ──────────────────────────────────────────────────────────

def process_book(
    file_path: str,
    domain_id: str,
    config_manager=None,
    max_pages: int = None,
    chunk_size: int = 4000,
    on_progress: callable = None
) -> Dict[str, Any]:
    """
    Process a document and extract knowledge entities to the ontology.
    
    Supported formats: PDF, DOCX, PPTX, XLSX, EPUB, HTML, TXT, MD
    Uses MarkItDown as primary extractor (offline, no API required).
    
    Args:
        file_path: Path to the document file
        domain_id: Target domain ID (e.g., 'excel', 'econometrics')
        config_manager: ConfigManager instance for AI profile access
        max_pages: Maximum pages to process (None = all, only applies to PDF)
        chunk_size: Characters per chunk for LLM processing
        on_progress: Callback function(current, total, message)
        
    Returns:
        dict with status, entities_created, relations_created, etc.
    """
    import time
    start_time = time.time()
    
    # Validate inputs
    if not os.path.isfile(file_path):
        return {"status": "error", "error": f"File not found: {file_path}"}
    
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.epub',
        '.html', '.htm', '.txt', '.md', '.csv', '.xml'
    }
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            "status": "error",
            "error": f"Format '{ext}' not supported. Use: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        }
    
    # Get domain info
    manager = get_manager()
    if domain_id not in manager.domains:
        # Try to find by display name
        found_id = _find_domain_by_name(domain_id)
        if found_id:
            domain_id = found_id
        else:
            # Create new domain automatically
            print(f"[Ontology] Creating new domain: {domain_id}")
            create_result = manager.create_domain(domain_id)
            if create_result.get("status") == "error":
                return create_result
            # Refresh manager to pick up new domain
            manager.discover_domains()
    
    domain = manager.domains[domain_id]
    graph_path = os.path.join(domain.path, "graph.jsonl")
    
    # Create graph.jsonl if it doesn't exist (for newly created domains)
    if not os.path.isfile(graph_path):
        os.makedirs(os.path.dirname(graph_path), exist_ok=True)
        with open(graph_path, 'w', encoding='utf-8') as f:
            pass  # Empty file
    
    # Step 1: Extract text from document
    if on_progress:
        on_progress(0, 100, f"Extracting text from {os.path.splitext(file_path)[1].upper()} file...")
    
    try:
        text_chunks = _extract_document_text(file_path, max_pages, chunk_size)
    except Exception as e:
        return {"status": "error", "error": f"Text extraction failed: {e}"}
    
    if not text_chunks:
        return {"status": "error", "error": "No text extracted from PDF"}
    
    # Step 2: Get AI profile
    if on_progress:
        on_progress(10, 100, "Loading AI profile...")
    
    ai_profile = _get_active_ai_profile(config_manager)
    if not ai_profile:
        return {"status": "error", "error": "No active AI profile configured. Go to Settings → Motor IA."}
    
    # Step 3: Load extraction prompt
    prompt_path = r"C:\NEVEN\prompts\ontology_extraction.txt"
    if not os.path.isfile(prompt_path):
        return {"status": "error", "error": f"Extraction prompt not found: {prompt_path}"}
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    
    # Step 4: Process chunks with LLM
    if on_progress:
        on_progress(15, 100, f"Processing {len(text_chunks)} text chunks...")
    
    all_entities = []
    all_relations = []
    
    for i, chunk in enumerate(text_chunks):
        progress = 15 + int((i / len(text_chunks)) * 70)
        if on_progress:
            on_progress(progress, 100, f"Processing chunk {i+1}/{len(text_chunks)}...")
        
        try:
            jsonl_output = _call_llm_for_extraction(
                ai_profile, 
                system_prompt, 
                chunk,
                book_name=os.path.basename(file_path)
            )
            
            # Parse JSONL output
            entities, relations = _parse_jsonl_output(jsonl_output)
            all_entities.extend(entities)
            all_relations.extend(relations)
            
        except Exception as e:
            # Log but continue with other chunks
            print(f"[OntologyManager] Chunk {i+1} failed: {e}")
    
    # Step 5: Deduplicate entities by ID
    if on_progress:
        on_progress(85, 100, "Deduplicating entities...")
    
    unique_entities = _deduplicate_entities(all_entities)
    
    # Step 6: Backup existing graph.jsonl
    if on_progress:
        on_progress(90, 100, "Creating backup...")
    
    _backup_graph_file(graph_path)
    
    # Step 7: Append to graph.jsonl
    if on_progress:
        on_progress(95, 100, "Writing to ontology...")
    
    entities_written = 0
    relations_written = 0
    
    with open(graph_path, 'a', encoding='utf-8') as f:
        for entity in unique_entities:
            f.write(json.dumps({"op": "create", "entity": entity}, ensure_ascii=False) + '\n')
            entities_written += 1
        
        for relation in all_relations:
            f.write(json.dumps({"op": "relate", "relation": relation}, ensure_ascii=False) + '\n')
            relations_written += 1
    
    # Step 8: Reload domain
    manager.load_domain(domain_id)
    
    elapsed = time.time() - start_time
    
    if on_progress:
        on_progress(100, 100, "Complete!")
    
    return {
        "status": "ok",
        "entities_created": entities_written,
        "relations_created": relations_written,
        "domain": domain_id,
        "book": os.path.basename(file_path),
        "chunks_processed": len(text_chunks),
        "processing_time_seconds": round(elapsed, 1)
    }


def _find_domain_by_name(name: str) -> Optional[str]:
    """Find domain ID by display name."""
    manager = get_manager()
    name_lower = name.lower().replace(" ", "_").replace("-", "_")
    
    for domain in manager.domains.values():
        if domain.id == name_lower:
            return domain.id
        if domain.name.lower().replace(" ", "_") == name_lower:
            return domain.id
        # Also check folder-style names
        if "libros_" + name_lower == domain.id:
            return domain.id
    
    return None


def _extract_document_text(file_path: str, max_pages: int = None, chunk_size: int = 4000) -> List[str]:
    """
    Extract text from any supported document format.

    Strategy:
    - PDF + max_pages → PyMuPDF (stops at page N, efficient for large books)
    - All other cases  → MarkItDown (handles PDF, DOCX, EPUB, PPTX, XLSX, HTML, TXT, MD…)
    - Plain text fallback if MarkItDown is not installed

    Supports: PDF, DOCX, PPTX, XLSX, XLS, EPUB, HTML, TXT, MD and more.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # PDF with page limit: use PyMuPDF — converts only the requested pages (efficient)
    if ext == '.pdf' and max_pages:
        return _extract_pdf_text(file_path, max_pages, chunk_size)

    # All other cases: use MarkItDown (supports 15+ formats offline, including full PDF)
    try:
        from markitdown import MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert(file_path)
        full_text = result.markdown.strip()
        if full_text:
            return _split_into_chunks(full_text, chunk_size)
    except ImportError:
        pass  # MarkItDown not installed — fall through to plain-text fallback
    except Exception as e:
        print(f"[Ontology] MarkItDown failed for {os.path.basename(file_path)}: {e}")

    # Last-resort fallback for plain text formats when MarkItDown is unavailable
    if ext in {'.txt', '.md', '.csv', '.xml', '.html', '.htm'}:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return _split_into_chunks(f.read(), chunk_size)

    raise ValueError(
        f"Cannot extract text from '{ext}'. "
        "Install MarkItDown: pip install 'markitdown[pdf,docx,pptx,xlsx,xls]' ebooklib"
    )


def _split_into_chunks(full_text: str, chunk_size: int = 4000) -> List[str]:
    """Split text into chunks at paragraph boundaries."""
    chunks = []
    current_chunk = ""
    paragraphs = full_text.split("\n\n")
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def _extract_pdf_text(file_path: str, max_pages: int = None, chunk_size: int = 4000) -> List[str]:
    """Extract text from PDF and split into chunks."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("PyMuPDF (fitz) is required. Install with: pip install pymupdf")
    
    doc = fitz.open(file_path)
    
    all_text = []
    pages_to_process = min(len(doc), max_pages) if max_pages else len(doc)
    
    for page_num in range(pages_to_process):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            all_text.append(text)
    
    doc.close()
    
    # Join all text and split into chunks
    full_text = "\n\n".join(all_text)
    
    # Split into chunks, trying to break at paragraph boundaries
    chunks = []
    current_chunk = ""
    
    paragraphs = full_text.split("\n\n")
    for para in paragraphs:
        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def _get_active_ai_profile(config_manager) -> Optional[Dict[str, Any]]:
    """Get the active AI profile from config_manager."""
    if config_manager is None:
        try:
            from config_manager import ConfigManager
            config_manager = ConfigManager()
        except ImportError:
            return None
    
    try:
        profiles = config_manager.list_ai_profiles()
        for profile in profiles:
            if profile.get("is_active"):
                return profile
    except Exception:
        pass
    
    return None


def _call_llm_for_extraction(
    ai_profile: Dict[str, Any],
    system_prompt: str,
    text_chunk: str,
    book_name: str = ""
) -> str:
    """Call the LLM to extract entities from a text chunk."""
    import requests
    
    provider = ai_profile.get("provider", "").lower()
    endpoint = ai_profile.get("endpoint", "")
    model = ai_profile.get("model", "")
    api_key = ai_profile.get("api_key", "")
    
    user_prompt = f"""Analiza el siguiente fragmento del libro "{book_name}" y extrae las entidades de conocimiento.

TEXTO:
{text_chunk}

INSTRUCCIONES:
- Genera SOLO líneas JSONL válidas (una por línea)
- No incluyas explicaciones, solo JSON
- Si no hay entidades relevantes en este fragmento, responde con una línea vacía"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Build request based on provider
    if provider in ("openai", "azure", "lmstudio"):
        if provider == "azure":
            url = endpoint
        elif provider == "lmstudio":
            url = endpoint or "http://localhost:1234/v1/chat/completions"
        else:
            url = endpoint or "https://api.openai.com/v1/chat/completions"
        
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    elif provider == "ollama":
        url = endpoint or "http://localhost:11434/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.3}
        }
        
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        return result.get("message", {}).get("content", "")
    
    elif provider == "anthropic":
        url = endpoint or "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result["content"][0]["text"]
    
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")


def _parse_jsonl_output(jsonl_text: str) -> tuple:
    """Parse JSONL output into entities and relations."""
    entities = []
    relations = []
    
    for line in jsonl_text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Handle markdown code blocks
        if line.startswith('```'):
            continue
        
        try:
            obj = json.loads(line)
            op = obj.get("op")
            
            if op == "create" and "entity" in obj:
                entities.append(obj["entity"])
            elif op == "relate" and "relation" in obj:
                relations.append(obj["relation"])
        except json.JSONDecodeError:
            # Skip invalid lines
            continue
    
    return entities, relations


def _deduplicate_entities(entities: List[Dict]) -> List[Dict]:
    """Remove duplicate entities by ID."""
    seen = set()
    unique = []
    
    for entity in entities:
        entity_id = entity.get("id")
        if entity_id and entity_id not in seen:
            seen.add(entity_id)
            unique.append(entity)
    
    return unique


def _backup_graph_file(graph_path: str):
    """Create a backup of the graph.jsonl file."""
    if not os.path.isfile(graph_path):
        return
    
    import shutil
    from datetime import datetime
    
    backup_dir = os.path.join(os.path.dirname(graph_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"graph_{timestamp}.jsonl"
    backup_path = os.path.join(backup_dir, backup_name)
    
    shutil.copy2(graph_path, backup_path)


def list_processed_books(domain_id: str = None) -> List[Dict[str, Any]]:
    """
    List books that have been processed for a domain (based on source_book references).
    
    Returns list of {book_name, domain, entity_count, first_seen}
    """
    manager = get_manager()
    books = {}
    
    domains_to_check = [domain_id] if domain_id else list(manager.domains.keys())
    
    for did in domains_to_check:
        if not manager.ensure_loaded(did):
            continue
        
        entities = manager._entities.get(did, {})
        for entity in entities.values():
            # Look for source_book or reference.book
            source = entity.properties.get("source_book")
            if not source:
                ref = entity.properties.get("reference", {})
                source = ref.get("book") if isinstance(ref, dict) else None
            
            if source:
                key = f"{did}:{source}"
                if key not in books:
                    books[key] = {
                        "book_name": source,
                        "domain": did,
                        "entity_count": 0
                    }
                books[key]["entity_count"] += 1
    
    return list(books.values())


# ─── Export ───────────────────────────────────────────────────────────────────

__all__ = [
    "OntologyManager",
    "OntologyDomain", 
    "Entity",
    "get_manager",
    "get_excel_function",
    "get_econometric_method",
    "search_knowledge",
    "process_book",
    "list_processed_books",
]
