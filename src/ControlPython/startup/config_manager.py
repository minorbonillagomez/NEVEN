# ═══════════════════════════════════════════════════════════════════════════════
# NEVEN Config Manager v2.0
# ═══════════════════════════════════════════════════════════════════════════════
# Manages NEVEN configuration with support for:
# - Multiple AI profiles (OpenAI, Azure, Anthropic, Ollama)
# - Multiple DB connections (PostgreSQL, MySQL, SQL Server, SQLite, DuckDB)
# - Secure credential storage via Windows Credential Manager (keyring)
# - Config versioning and migration from v1 to v2
#
# Credentials are NEVER stored in the JSON file — only references to keyring keys.
# ═══════════════════════════════════════════════════════════════════════════════

import os
import json
import uuid
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

# ─── Keyring for Windows Credential Manager ───────────────────────────────────
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None  # type: ignore

# ─── AI Provider client libraries (for test connection) ──────────────────────
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger("NEVEN.ConfigManager")

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

CONFIG_VERSION = "2.0"
KEYRING_SERVICE = "NEVEN"
DEFAULT_CONFIG_PATH = r"C:\NEVEN\neven-config.json"

AI_PROVIDERS = ["openai", "azure", "anthropic", "ollama"]
AI_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "azure": ["gpt-4o", "gpt-4.1", "gpt-4-turbo", "gpt-35-turbo"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    "ollama": ["llama3", "llama3.1", "mistral", "codellama", "phi3"],
}

DB_TYPES = ["postgresql", "mysql", "sqlserver", "sqlite", "duckdb"]
DB_DEFAULT_PORTS = {
    "postgresql": 5432,
    "mysql": 3306,
    "sqlserver": 1433,
    "sqlite": None,
    "duckdb": None,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AIProfile:
    """Configuration for an AI provider profile."""
    id: str
    name: str
    provider: str  # openai, azure, anthropic, ollama
    model: str
    endpoint: Optional[str] = None  # Required for Azure, optional for others
    api_version: Optional[str] = None  # Azure only
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DBConnection:
    """Configuration for a database connection."""
    id: str
    name: str
    db_type: str  # postgresql, mysql, sqlserver, sqlite, duckdb
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    use_windows_auth: bool = False  # SQL Server only
    extra_params: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DBConnection":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        if "extra_params" not in fields:
            fields["extra_params"] = {}
        return cls(**fields)


@dataclass 
class PromptConfig:
    """Configuration for system prompts."""
    active_system: str = "default"
    prompts_directory: str = r"C:\NEVEN\prompts"
    custom_prompts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Preferences:
    """User preferences."""
    language: str = "es"
    theme: str = "system"  # light, dark, system
    log_level: str = "info"
    auto_start_engines: List[str] = field(default_factory=lambda: ["python"])
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════════════
# Config Manager
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """
    Manages NEVEN configuration with secure credential storage.
    
    Usage:
        mgr = ConfigManager()
        mgr.load()
        
        # List AI profiles
        profiles = mgr.list_ai_profiles()
        
        # Add new profile
        profile_id = mgr.add_ai_profile("My OpenAI", "openai", "gpt-4o", api_key="sk-...")
        
        # Set active
        mgr.set_active_ai_profile(profile_id)
        
        # Save
        mgr.save()
    """
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.version = CONFIG_VERSION
        
        # Active selections
        self.active_ai_profile: Optional[str] = None
        self.active_db_connection: Optional[str] = None
        
        # Collections
        self.ai_profiles: Dict[str, AIProfile] = {}
        self.db_connections: Dict[str, DBConnection] = {}
        
        # Other config
        self.prompts = PromptConfig()
        self.preferences = Preferences()
        
        # Legacy config (preserved for backward compatibility)
        self._legacy_config: Dict[str, Any] = {}
    
    # ─── Load / Save ──────────────────────────────────────────────────────────
    
    def load(self) -> bool:
        """Load configuration from file. Returns True if successful."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check version
            version = data.get("version", "1.0")
            
            if version.startswith("2."):
                self._load_v2(data)
            else:
                self._migrate_v1_to_v2(data)
            
            logger.info(f"Config loaded from {self.config_path} (version {version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def _load_v2(self, data: Dict[str, Any]) -> None:
        """Load v2 format config."""
        self.version = data.get("version", CONFIG_VERSION)
        self.active_ai_profile = data.get("active_ai_profile")
        self.active_db_connection = data.get("active_db_connection")
        
        # Load AI profiles
        for p in data.get("ai_profiles", []):
            profile = AIProfile.from_dict(p)
            self.ai_profiles[profile.id] = profile
        
        # Load DB connections
        for c in data.get("db_connections", []):
            conn = DBConnection.from_dict(c)
            self.db_connections[conn.id] = conn
        
        # Load prompts
        if "prompts" in data:
            self.prompts = PromptConfig(**data["prompts"])
        
        # Load preferences
        if "preferences" in data:
            self.preferences = Preferences(**data["preferences"])
        
        # Preserve legacy sections
        for key in ["NEVEN", "WebView2", "Pluto", "TaskPane", "Standalone"]:
            if key in data:
                self._legacy_config[key] = data[key]
    
    def _migrate_v1_to_v2(self, data: Dict[str, Any]) -> None:
        """Migrate v1 config to v2 format, preserving existing AI config."""
        logger.info("Migrating config from v1 to v2...")
        
        # Preserve all legacy sections
        for key in ["NEVEN", "WebView2", "Pluto", "TaskPane", "Standalone", "auto_load_xll"]:
            if key in data:
                self._legacy_config[key] = data[key]
        
        # Migrate AI section to a profile
        if "AI" in data:
            ai = data["AI"]
            if ai.get("enabled", False) and ai.get("apiKey"):
                profile_id = f"{ai.get('provider', 'openai')}-migrated"
                profile = AIProfile(
                    id=profile_id,
                    name=f"{ai.get('provider', 'OpenAI').title()} (Migrado)",
                    provider=ai.get("provider", "openai"),
                    model=ai.get("model", "gpt-4o"),
                    endpoint=ai.get("endpoint"),
                    api_version=ai.get("apiVersion"),
                    temperature=ai.get("temperature", 0.7),
                    max_tokens=ai.get("maxTokens", 4096),
                    timeout=ai.get("timeout", 120),
                )
                self.ai_profiles[profile_id] = profile
                self.active_ai_profile = profile_id
                
                # Store API key in keyring
                api_key = ai.get("apiKey", "")
                if api_key and KEYRING_AVAILABLE:
                    self._set_credential(f"ai/{profile_id}", api_key)
                    logger.info(f"Migrated API key to Windows Credential Manager")
        
        # Migrate prompts directory
        if "AI" in data and "promptsDirectory" in data["AI"]:
            self.prompts.prompts_directory = data["AI"]["promptsDirectory"]
    
    def save(self) -> bool:
        """Save configuration to file. Returns True if successful."""
        try:
            data = self._to_dict()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Config saved to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def _to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization."""
        data = {
            "version": self.version,
            "active_ai_profile": self.active_ai_profile,
            "active_db_connection": self.active_db_connection,
            "ai_profiles": [p.to_dict() for p in self.ai_profiles.values()],
            "db_connections": [c.to_dict() for c in self.db_connections.values()],
            "prompts": self.prompts.to_dict(),
            "preferences": self.preferences.to_dict(),
        }
        
        # Include legacy sections
        data.update(self._legacy_config)
        
        return data
    
    # ─── Credential Management ────────────────────────────────────────────────
    
    def _get_credential(self, key: str) -> Optional[str]:
        """Get credential from Windows Credential Manager."""
        if not KEYRING_AVAILABLE:
            logger.warning("keyring not available — credentials will not be stored securely")
            return None
        try:
            return keyring.get_password(KEYRING_SERVICE, key)
        except Exception as e:
            logger.error(f"Failed to get credential {key}: {e}")
            return None
    
    def _set_credential(self, key: str, value: str) -> bool:
        """Store credential in Windows Credential Manager."""
        if not KEYRING_AVAILABLE:
            logger.warning("keyring not available — credential not stored")
            return False
        try:
            keyring.set_password(KEYRING_SERVICE, key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set credential {key}: {e}")
            return False
    
    def _delete_credential(self, key: str) -> bool:
        """Delete credential from Windows Credential Manager."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.delete_password(KEYRING_SERVICE, key)
            return True
        except Exception as e:
            logger.debug(f"Failed to delete credential {key}: {e}")
            return False
    
    # ─── AI Profile Management ────────────────────────────────────────────────
    
    def list_ai_profiles(self) -> List[Dict[str, Any]]:
        """List all AI profiles with active flag."""
        result = []
        for p in self.ai_profiles.values():
            d = p.to_dict()
            d["active"] = (p.id == self.active_ai_profile)
            d["has_api_key"] = self._get_credential(f"ai/{p.id}") is not None
            result.append(d)
        return result
    
    def get_ai_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get a single AI profile by ID."""
        if profile_id not in self.ai_profiles:
            return None
        p = self.ai_profiles[profile_id]
        d = p.to_dict()
        d["active"] = (p.id == self.active_ai_profile)
        d["has_api_key"] = self._get_credential(f"ai/{p.id}") is not None
        return d
    
    def get_active_ai_profile(self) -> Optional[Dict[str, Any]]:
        """Get the currently active AI profile with decrypted API key."""
        if not self.active_ai_profile:
            return None
        if self.active_ai_profile not in self.ai_profiles:
            return None
        
        p = self.ai_profiles[self.active_ai_profile]
        d = p.to_dict()
        d["active"] = True
        d["api_key"] = self._get_credential(f"ai/{p.id}")
        return d
    
    def add_ai_profile(
        self,
        name: str,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 120,
        set_active: bool = False,
    ) -> str:
        """Add a new AI profile. Returns the profile ID."""
        profile_id = f"{provider}-{uuid.uuid4().hex[:8]}"
        
        profile = AIProfile(
            id=profile_id,
            name=name,
            provider=provider,
            model=model,
            endpoint=endpoint,
            api_version=api_version,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        
        self.ai_profiles[profile_id] = profile
        
        if api_key:
            self._set_credential(f"ai/{profile_id}", api_key)
        
        if set_active or not self.active_ai_profile:
            self.active_ai_profile = profile_id
        
        return profile_id
    
    def update_ai_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> bool:
        """Update an existing AI profile. Returns True if successful."""
        if profile_id not in self.ai_profiles:
            return False
        
        p = self.ai_profiles[profile_id]
        
        if name is not None:
            p.name = name
        if provider is not None:
            p.provider = provider
        if model is not None:
            p.model = model
        if endpoint is not None:
            p.endpoint = endpoint
        if api_version is not None:
            p.api_version = api_version
        if temperature is not None:
            p.temperature = temperature
        if max_tokens is not None:
            p.max_tokens = max_tokens
        if timeout is not None:
            p.timeout = timeout
        
        if api_key is not None:
            self._set_credential(f"ai/{profile_id}", api_key)
        
        return True
    
    def delete_ai_profile(self, profile_id: str) -> bool:
        """Delete an AI profile. Returns True if successful."""
        if profile_id not in self.ai_profiles:
            return False
        
        del self.ai_profiles[profile_id]
        self._delete_credential(f"ai/{profile_id}")
        
        if self.active_ai_profile == profile_id:
            # Set first remaining profile as active, or None
            self.active_ai_profile = next(iter(self.ai_profiles.keys()), None)
        
        return True
    
    def set_active_ai_profile(self, profile_id: str) -> bool:
        """Set the active AI profile."""
        if profile_id not in self.ai_profiles:
            return False
        self.active_ai_profile = profile_id
        return True
    
    # ─── DB Connection Management ─────────────────────────────────────────────
    
    def list_db_connections(self) -> List[Dict[str, Any]]:
        """List all DB connections with active flag."""
        result = []
        for c in self.db_connections.values():
            d = c.to_dict()
            d["active"] = (c.id == self.active_db_connection)
            d["has_password"] = self._get_credential(f"db/{c.id}") is not None
            result.append(d)
        return result
    
    def get_db_connection(self, conn_id: str) -> Optional[Dict[str, Any]]:
        """Get a single DB connection by ID."""
        if conn_id not in self.db_connections:
            return None
        c = self.db_connections[conn_id]
        d = c.to_dict()
        d["active"] = (c.id == self.active_db_connection)
        d["has_password"] = self._get_credential(f"db/{c.id}") is not None
        return d
    
    def get_active_db_connection(self) -> Optional[Dict[str, Any]]:
        """Get the currently active DB connection with decrypted password."""
        if not self.active_db_connection:
            return None
        if self.active_db_connection not in self.db_connections:
            return None
        
        c = self.db_connections[self.active_db_connection]
        d = c.to_dict()
        d["active"] = True
        d["password"] = self._get_credential(f"db/{c.id}")
        return d
    
    def add_db_connection(
        self,
        name: str,
        db_type: str,
        database: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_windows_auth: bool = False,
        extra_params: Optional[Dict[str, str]] = None,
        set_active: bool = False,
    ) -> str:
        """Add a new DB connection. Returns the connection ID."""
        conn_id = f"{db_type}-{uuid.uuid4().hex[:8]}"
        
        # Set default port if not provided
        if port is None:
            port = DB_DEFAULT_PORTS.get(db_type)
        
        conn = DBConnection(
            id=conn_id,
            name=name,
            db_type=db_type,
            host=host,
            port=port,
            database=database,
            username=username,
            use_windows_auth=use_windows_auth,
            extra_params=extra_params or {},
        )
        
        self.db_connections[conn_id] = conn
        
        if password:
            self._set_credential(f"db/{conn_id}", password)
        
        if set_active or not self.active_db_connection:
            self.active_db_connection = conn_id
        
        return conn_id
    
    def update_db_connection(
        self,
        conn_id: str,
        name: Optional[str] = None,
        db_type: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_windows_auth: Optional[bool] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Update an existing DB connection. Returns True if successful."""
        if conn_id not in self.db_connections:
            return False
        
        c = self.db_connections[conn_id]
        
        if name is not None:
            c.name = name
        if db_type is not None:
            c.db_type = db_type
        if host is not None:
            c.host = host
        if port is not None:
            c.port = port
        if database is not None:
            c.database = database
        if username is not None:
            c.username = username
        if use_windows_auth is not None:
            c.use_windows_auth = use_windows_auth
        if extra_params is not None:
            c.extra_params = extra_params
        
        if password is not None:
            self._set_credential(f"db/{conn_id}", password)
        
        return True
    
    def delete_db_connection(self, conn_id: str) -> bool:
        """Delete a DB connection. Returns True if successful."""
        if conn_id not in self.db_connections:
            return False
        
        del self.db_connections[conn_id]
        self._delete_credential(f"db/{conn_id}")
        
        if self.active_db_connection == conn_id:
            self.active_db_connection = next(iter(self.db_connections.keys()), None)
        
        return True
    
    def set_active_db_connection(self, conn_id: str) -> bool:
        """Set the active DB connection."""
        if conn_id not in self.db_connections:
            return False
        self.active_db_connection = conn_id
        return True
    
    # ─── Test Connections ─────────────────────────────────────────────────────
    
    def test_ai_connection(self, profile_id: str) -> Dict[str, Any]:
        """
        Test AI provider connection without making expensive API calls.
        Returns {"success": bool, "message": str, "details": dict}
        """
        if profile_id not in self.ai_profiles:
            return {"success": False, "message": "Perfil no encontrado", "details": {}}
        
        profile = self.ai_profiles[profile_id]
        api_key = self._get_credential(f"ai/{profile_id}")
        
        if not api_key:
            return {"success": False, "message": "API Key no configurada", "details": {}}
        
        if not HTTPX_AVAILABLE:
            return {"success": False, "message": "httpx no disponible para test", "details": {}}
        
        try:
            if profile.provider == "openai":
                return self._test_openai(api_key, profile)
            elif profile.provider == "azure":
                return self._test_azure(api_key, profile)
            elif profile.provider == "anthropic":
                return self._test_anthropic(api_key, profile)
            elif profile.provider == "ollama":
                return self._test_ollama(profile)
            else:
                return {"success": False, "message": f"Proveedor desconocido: {profile.provider}", "details": {}}
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_openai(self, api_key: str, profile: AIProfile) -> Dict[str, Any]:
        """Test OpenAI connection by listing models."""
        url = "https://api.openai.com/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
        
        if resp.status_code == 200:
            models = [m["id"] for m in resp.json().get("data", [])]
            model_exists = profile.model in models
            return {
                "success": True,
                "message": "Conexion exitosa" if model_exists else f"Conexion OK pero modelo '{profile.model}' no encontrado",
                "details": {"models_available": len(models), "model_exists": model_exists}
            }
        elif resp.status_code == 401:
            return {"success": False, "message": "API Key invalida", "details": {}}
        else:
            return {"success": False, "message": f"Error HTTP {resp.status_code}", "details": {"body": resp.text[:200]}}
    
    def _test_azure(self, api_key: str, profile: AIProfile) -> Dict[str, Any]:
        """Test Azure OpenAI connection."""
        if not profile.endpoint:
            return {"success": False, "message": "Endpoint no configurado", "details": {}}
        
        # Azure uses different auth header
        url = f"{profile.endpoint.rstrip('/')}/openai/deployments?api-version={profile.api_version or '2024-02-15-preview'}"
        headers = {"api-key": api_key}
        
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
        
        if resp.status_code == 200:
            deployments = resp.json().get("data", [])
            return {
                "success": True,
                "message": f"Conexion exitosa ({len(deployments)} deployments)",
                "details": {"deployments": [d.get("id") for d in deployments]}
            }
        elif resp.status_code == 401:
            return {"success": False, "message": "API Key invalida", "details": {}}
        else:
            return {"success": False, "message": f"Error HTTP {resp.status_code}", "details": {"body": resp.text[:200]}}
    
    def _test_anthropic(self, api_key: str, profile: AIProfile) -> Dict[str, Any]:
        """Test Anthropic connection with minimal request."""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Send minimal request that will fail validation but confirm auth works
        body = {"model": profile.model, "max_tokens": 1, "messages": []}
        
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, headers=headers, json=body)
        
        # 400 with "messages" error means auth worked but request invalid (expected)
        # 401 means bad API key
        if resp.status_code == 400 and "messages" in resp.text.lower():
            return {"success": True, "message": "Conexion exitosa (API key valida)", "details": {}}
        elif resp.status_code == 401:
            return {"success": False, "message": "API Key invalida", "details": {}}
        else:
            return {"success": False, "message": f"Error HTTP {resp.status_code}", "details": {"body": resp.text[:200]}}
    
    def _test_ollama(self, profile: AIProfile) -> Dict[str, Any]:
        """Test Ollama local connection."""
        endpoint = profile.endpoint or "http://localhost:11434"
        url = f"{endpoint.rstrip('/')}/api/tags"
        
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(url)
            
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                model_exists = any(profile.model in m for m in models)
                return {
                    "success": True,
                    "message": "Ollama conectado" if model_exists else f"Ollama OK pero modelo '{profile.model}' no instalado",
                    "details": {"models": models, "model_exists": model_exists}
                }
            else:
                return {"success": False, "message": f"Error HTTP {resp.status_code}", "details": {}}
        except httpx.ConnectError:
            return {"success": False, "message": "Ollama no esta corriendo en " + endpoint, "details": {}}
    
    def test_db_connection(self, conn_id: str) -> Dict[str, Any]:
        """
        Test database connection.
        Returns {"success": bool, "message": str, "details": dict}
        """
        if conn_id not in self.db_connections:
            return {"success": False, "message": "Conexion no encontrada", "details": {}}
        
        conn = self.db_connections[conn_id]
        password = self._get_credential(f"db/{conn_id}")
        
        try:
            if conn.db_type == "sqlite":
                return self._test_sqlite(conn)
            elif conn.db_type == "duckdb":
                return self._test_duckdb(conn)
            elif conn.db_type == "postgresql":
                return self._test_postgresql(conn, password)
            elif conn.db_type == "mysql":
                return self._test_mysql(conn, password)
            elif conn.db_type == "sqlserver":
                return self._test_sqlserver(conn, password)
            else:
                return {"success": False, "message": f"Tipo DB desconocido: {conn.db_type}", "details": {}}
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_sqlite(self, conn: DBConnection) -> Dict[str, Any]:
        """Test SQLite connection."""
        import sqlite3
        
        db_path = conn.database
        if not os.path.exists(db_path):
            return {"success": False, "message": f"Archivo no existe: {db_path}", "details": {}}
        
        try:
            with sqlite3.connect(db_path) as c:
                tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            return {
                "success": True,
                "message": f"Conectado ({len(tables)} tablas)",
                "details": {"tables": [t[0] for t in tables]}
            }
        except sqlite3.Error as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_duckdb(self, conn: DBConnection) -> Dict[str, Any]:
        """Test DuckDB connection."""
        try:
            import duckdb
        except ImportError:
            return {"success": False, "message": "duckdb no instalado", "details": {}}
        
        db_path = conn.database or ":memory:"
        
        try:
            with duckdb.connect(db_path) as c:
                tables = c.execute("SHOW TABLES").fetchall()
            return {
                "success": True,
                "message": f"Conectado ({len(tables)} tablas)",
                "details": {"tables": [t[0] for t in tables]}
            }
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_postgresql(self, conn: DBConnection, password: Optional[str]) -> Dict[str, Any]:
        """Test PostgreSQL connection."""
        try:
            import psycopg2
        except ImportError:
            return {"success": False, "message": "psycopg2 no instalado", "details": {}}
        
        try:
            with psycopg2.connect(
                host=conn.host,
                port=conn.port or 5432,
                database=conn.database,
                user=conn.username,
                password=password,
                connect_timeout=5,
            ) as c:
                with c.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
            return {"success": True, "message": "Conectado", "details": {"version": version}}
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_mysql(self, conn: DBConnection, password: Optional[str]) -> Dict[str, Any]:
        """Test MySQL connection."""
        try:
            import mysql.connector
        except ImportError:
            return {"success": False, "message": "mysql-connector-python no instalado", "details": {}}
        
        try:
            with mysql.connector.connect(
                host=conn.host,
                port=conn.port or 3306,
                database=conn.database,
                user=conn.username,
                password=password,
                connection_timeout=5,
            ) as c:
                with c.cursor() as cur:
                    cur.execute("SELECT VERSION()")
                    version = cur.fetchone()[0]
            return {"success": True, "message": "Conectado", "details": {"version": version}}
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    def _test_sqlserver(self, conn: DBConnection, password: Optional[str]) -> Dict[str, Any]:
        """Test SQL Server connection."""
        try:
            import pyodbc
        except ImportError:
            return {"success": False, "message": "pyodbc no instalado", "details": {}}
        
        driver = conn.extra_params.get("driver", "ODBC Driver 17 for SQL Server")
        
        if conn.use_windows_auth:
            conn_str = f"DRIVER={{{driver}}};SERVER={conn.host},{conn.port or 1433};DATABASE={conn.database};Trusted_Connection=yes"
        else:
            conn_str = f"DRIVER={{{driver}}};SERVER={conn.host},{conn.port or 1433};DATABASE={conn.database};UID={conn.username};PWD={password}"
        
        try:
            with pyodbc.connect(conn_str, timeout=5) as c:
                with c.cursor() as cur:
                    cur.execute("SELECT @@VERSION")
                    version = cur.fetchone()[0]
            return {"success": True, "message": "Conectado", "details": {"version": version[:100]}}
        except Exception as e:
            return {"success": False, "message": str(e), "details": {}}
    
    # ─── Static helpers ───────────────────────────────────────────────────────
    
    @staticmethod
    def get_ai_providers() -> List[str]:
        """Get list of supported AI providers."""
        return AI_PROVIDERS
    
    @staticmethod
    def get_ai_models(provider: str) -> List[str]:
        """Get list of models for a provider."""
        return AI_MODELS.get(provider, [])
    
    @staticmethod
    def get_db_types() -> List[str]:
        """Get list of supported database types."""
        return DB_TYPES
    
    @staticmethod
    def get_db_default_port(db_type: str) -> Optional[int]:
        """Get default port for a database type."""
        return DB_DEFAULT_PORTS.get(db_type)


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton instance
# ═══════════════════════════════════════════════════════════════════════════════

_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: str = DEFAULT_CONFIG_PATH) -> ConfigManager:
    """Get or create the singleton ConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
        _config_manager.load()
    return _config_manager


def reload_config() -> ConfigManager:
    """Force reload of configuration."""
    global _config_manager
    _config_manager = None
    return get_config_manager()


# ═══════════════════════════════════════════════════════════════════════════════
# CLI for testing
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    logging.basicConfig(level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(description="NEVEN Config Manager CLI")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Config file path")
    parser.add_argument("--list-ai", action="store_true", help="List AI profiles")
    parser.add_argument("--list-db", action="store_true", help="List DB connections")
    parser.add_argument("--test-ai", metavar="ID", help="Test AI profile connection")
    parser.add_argument("--test-db", metavar="ID", help="Test DB connection")
    
    args = parser.parse_args()
    
    mgr = ConfigManager(args.config)
    mgr.load()
    
    if args.list_ai:
        print("\nAI Profiles:")
        for p in mgr.list_ai_profiles():
            active = "[ACTIVE]" if p["active"] else ""
            key = "[KEY OK]" if p["has_api_key"] else "[NO KEY]"
            print(f"  {p['id']}: {p['name']} ({p['provider']}/{p['model']}) {active} {key}")
    
    if args.list_db:
        print("\nDB Connections:")
        for c in mgr.list_db_connections():
            active = "[ACTIVE]" if c["active"] else ""
            pwd = "[PWD OK]" if c["has_password"] else "[NO PWD]"
            print(f"  {c['id']}: {c['name']} ({c['db_type']}) {active} {pwd}")
    
    if args.test_ai:
        result = mgr.test_ai_connection(args.test_ai)
        print(f"\nTest AI '{args.test_ai}': {result}")
    
    if args.test_db:
        result = mgr.test_db_connection(args.test_db)
        print(f"\nTest DB '{args.test_db}': {result}")
