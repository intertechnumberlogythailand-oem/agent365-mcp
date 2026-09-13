"""
config.py
Centralized configuration management for Agent365 MCP
Supports both local environment variables and GCP Secret Manager
"""

import os
from typing import Optional

# ── GCP Secret Manager Integration ──────────────────────────────────────────

try:
    from google.cloud import secretmanager
    HAS_GCP = True
except ImportError:
    HAS_GCP = False


def get_gcp_secret(secret_id: str, project_id: str = "intertechnumberlogythailand") -> str:
    """
    Helper to fetch secret payloads directly from GCP Secret Manager.
    Falls back to environment variables if GCP is not available.
    
    Args:
        secret_id: The secret identifier in GCP Secret Manager
        project_id: GCP project ID (default: intertechnumberlogythailand)
        
    Returns:
        Secret value from GCP or environment variable
    """
    if not HAS_GCP:
        return os.getenv(secret_id, "")
    
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"[!] Warning: Could not fetch secret '{secret_id}' from Secret Manager: {e}")
        # Fallback to local environment variable if executing locally
        return os.getenv(secret_id, "")


# ── Azure / Dataverse Configuration ─────────────────────────────────────────

TENANT_ID = os.getenv(
    "AZURE_TENANT_ID",
    get_gcp_secret("AZURE_TENANT_ID") or "<YOUR_TENANT_ID>"
)

CLIENT_ID = os.getenv(
    "AZURE_CLIENT_ID",
    get_gcp_secret("AZURE_CLIENT_ID") or "<YOUR_CLIENT_ID>"
)

CLIENT_SECRET = os.getenv(
    "AZURE_CLIENT_SECRET",
    get_gcp_secret("AZURE_CLIENT_SECRET") or "<YOUR_CLIENT_SECRET>"
)

DATAVERSE_ENV = os.getenv(
    "DATAVERSE_ENV",
    "https://intertechnumberlogythailand.crm5.dynamics.com"
)

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [f"{DATAVERSE_ENV}/.default"]


# ── MCP Server Configuration ────────────────────────────────────────────────

MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "intertechnumberlogythailand")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_RELOAD = os.getenv("MCP_SERVER_RELOAD", "true").lower() == "true"


# ── Stripe Configuration ────────────────────────────────────────────────────

STRIPE_PUBLIC_KEY = os.getenv(
    "STRIPE_PUBLIC_KEY",
    get_gcp_secret("STRIPE_PUBLIC_KEY") or ""
)

STRIPE_SECRET_KEY = os.getenv(
    "STRIPE_SECRET_KEY",
    get_gcp_secret("STRIPE_SECRET_KEY") or ""
)

STRIPE_WEBHOOK_SECRET = os.getenv(
    "STRIPE_WEBHOOK_SECRET",
    get_gcp_secret("STRIPE_WEBHOOK_SECRET") or ""
)


# ── Dataverse OData Configuration ───────────────────────────────────────────

DATAVERSE_API_VERSION = "v9.2"
DATAVERSE_ENTITY_SET = os.getenv("DATAVERSE_ENTITY_SET", "cr_aimodelses")
DATAVERSE_TIMEOUT = int(os.getenv("DATAVERSE_TIMEOUT", "60"))


# ── Logging Configuration ───────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json or text


# ── Feature Flags ───────────────────────────────────────────────────────────

ENABLE_METADATA_CACHING = os.getenv("ENABLE_METADATA_CACHING", "true").lower() == "true"
METADATA_CACHE_TTL = int(os.getenv("METADATA_CACHE_TTL", "3600"))  # 1 hour


# ── Validation ──────────────────────────────────────────────────────────────

def validate_config() -> bool:
    """
    Validate that all required configuration is present.
    
    Returns:
        True if config is valid, False otherwise
    """
    required = [
        ("TENANT_ID", TENANT_ID),
        ("CLIENT_ID", CLIENT_ID),
        ("CLIENT_SECRET", CLIENT_SECRET),
        ("DATAVERSE_ENV", DATAVERSE_ENV),
    ]
    
    missing = []
    for name, value in required:
        if not value or value.startswith("<YOUR_"):
            missing.append(name)
    
    if missing:
        print(f"[!] Missing required configuration: {', '.join(missing)}")
        print(f"[!] Set these as environment variables or in GCP Secret Manager")
        return False
    
    return True


# ── Configuration Summary ───────────────────────────────────────────────────

def print_config_summary() -> None:
    """Print non-sensitive configuration for debugging."""
    print(f"""
    ╔════════════════════════════════════════════════════╗
    ║  Agent365 Configuration Summary                    ║
    ╠════════════════════════════════════════════════════╣
    ║  MCP Server      : {MCP_SERVER_NAME:<32} ║
    ║  Port            : {MCP_SERVER_PORT:<32} ║
    ║  Dataverse       : {DATAVERSE_ENV[-40:]:<32} ║
    ║  Entity Set      : {DATAVERSE_ENTITY_SET:<32} ║
    ║  Log Level       : {LOG_LEVEL:<32} ║
    ║  GCP Integration : {('Yes' if HAS_GCP else 'No'):<32} ║
    ╚════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    print_config_summary()
    if validate_config():
        print("[✓] Configuration is valid")
    else:
        print("[✗] Configuration is incomplete")
