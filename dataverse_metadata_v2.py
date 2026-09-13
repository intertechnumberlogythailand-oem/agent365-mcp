"""
dataverse_metadata_v2.py
Builds on user's existing fetch script — adds XML parsing for cr_aimodels.
Intertech Numberology Thailand / Agent365
"""

import os
import xml.etree.ElementTree as ET
from typing import Optional

import msal
import requests

# ── Config (same as user's existing script) ───────────────────────────────────

TENANT_ID      = os.getenv("AZURE_TENANT_ID",    "<YOUR_TENANT_ID>")
CLIENT_ID      = os.getenv("AZURE_CLIENT_ID",    "<YOUR_CLIENT_ID>")
CLIENT_SECRET  = os.getenv("AZURE_CLIENT_SECRET","<YOUR_CLIENT_SECRET>")
DATAVERSE_ENV  = "https://intertechnumberlogythailand.crm5.dynamics.com"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE     = [f"{DATAVERSE_ENV}/.default"]

# Module-level singleton → preserves MSAL's internal token cache across calls
_msal_app: Optional[msal.ConfidentialClientApplication] = None

def _get_msal_app() -> msal.ConfidentialClientApplication:
    global _msal_app
    if _msal_app is None:
        _msal_app = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
        )
    return _msal_app


def get_access_token() -> str:
    """Acquire token — cache-first (no change to your existing logic)."""
    app    = _get_msal_app()
    result = app.acquire_token_silent(SCOPE, account=None)
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" in result:
        return result["access_token"]
    raise Exception(f"Token error: {result.get('error_description')}")


# ── Fetch (improved from user's version) ─────────────────────────────────────

def fetch_metadata(save_path: str = "dataverse_metadata.xml") -> str:
    """
    3 small improvements over original:
      1. timeout=60              → prevents hanging forever
      2. raise_for_status()      → cleaner than checking status_code manually
      3. Prefer header           → ensures ALL annotations are returned
    """
    token   = get_access_token()
    headers = {
        "Authorization":    f"Bearer {token}",
        "Accept":           "application/xml",
        "OData-MaxVersion": "4.0",
        "OData-Version":    "4.0",
        "Prefer":           "odata.include-annotations=*",   # ← NEW
    }
    url = f"{DATAVERSE_ENV}/api/data/v9.2/$metadata?annotations=true"
    print(f"Fetching: {url}")

    resp = requests.get(url, headers=headers, timeout=60)   # ← timeout added
    resp.raise_for_status()                                  # ← cleaner error

    with open(save_path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"[✓] Saved → {save_path}  ({len(resp.text):,} chars)")
    return resp.text


# ── Parse EDMX → cr_aimodels ─────────────────────────────────────────────────

NS = {
    "edm":  "http://docs.oasis-open.org/odata/ns/edm",
    "edmx": "http://docs.oasis-open.org/odata/ns/edmx",
}


def parse_cr_aimodels(xml_text: str) -> dict:
    """
    Walk the EDMX and return cr_aimodels schema.
    Also lists any other cr_* tables found — useful if the table name
    has a version suffix (e.g. cr8a2_aimodels).
    """
    root = ET.fromstring(xml_text)

    # ── A. Find all custom publisher entities (cr_* / new_*) ──────────────
    custom = [
        et.get("Name")
        for et in root.findall(".//edm:EntityType", NS)
        if et.get("Name", "").startswith(("cr_", "new_"))
    ]
    print(f"\n[Custom entities found: {len(custom)}]")
    for name in sorted(custom):
        print(f"  • {name}")

    # ── B. Locate cr_aimodels (or fuzzy match) ────────────────────────────
    target_et = None
    for et in root.findall(".//edm:EntityType", NS):
        if et.get("Name") == "cr_aimodels":
            target_et = et
            break

    if target_et is None:
        # Fuzzy: look for 'aimodel' in any cr_ entity
        for et in root.findall(".//edm:EntityType", NS):
            if "aimodel" in et.get("Name", "").lower():
                target_et = et
                print(f"\n[~] Fuzzy match: '{et.get('Name')}' (not exactly 'cr_aimodels')")
                break

    if target_et is None:
        return {
            "error": "cr_aimodels not found",
            "hint":  "Check publisher prefix above — may be cr8a2_ or similar",
            "custom_entities": custom,
        }

    entity_name = target_et.get("Name")

    # ── C. Resolve EntitySet name (used in REST calls) ────────────────────
    entity_set = None
    container  = root.find(".//edm:EntityContainer", NS)
    if container is not None:
        for es in container.findall("edm:EntitySet", NS):
            ref = es.get("EntityType", "")
            if ref.endswith(f".{entity_name}") or ref == entity_name:
                entity_set = es.get("Name")
                break

    # ── D. Extract properties ─────────────────────────────────────────────
    properties = []
    for prop in target_et.findall("edm:Property", NS):
        properties.append({
            "logical_name":  prop.get("Name"),
            "type":          prop.get("Type"),
            "nullable":      prop.get("Nullable", "true") != "false",
            "max_length":    prop.get("MaxLength"),
        })

    # ── E. Extract navigation properties (lookups) ────────────────────────
    nav_props = [
        {
            "name":    nav.get("Name"),
            "type":    nav.get("Type"),
            "partner": nav.get("Partner"),
        }
        for nav in target_et.findall("edm:NavigationProperty", NS)
    ]

    return {
        "entity_type":   entity_name,
        "entity_set":    entity_set,
        "primary_key":   (target_et.find(".//edm:PropertyRef", NS) or {}).get("Name"),
        "base_type":     target_et.get("BaseType"),
        "properties":    properties,
        "nav_properties": nav_props,
        "custom_entities_in_org": custom,
    }


# ── Print summary ─────────────────────────────────────────────────────────────

def print_schema(schema: dict) -> None:
    if "error" in schema:
        print(f"\n⚠  {schema['error']}")
        print(f"   {schema.get('hint','')}")
        return

    print(f"""
╔══ cr_aimodels Schema ═══════════════════════════════════════╗
  EntityType  : {schema['entity_type']}
  EntitySet   : {schema['entity_set']}   ← use in API calls
  Primary Key : {schema['primary_key']}
  Base Type   : {schema['base_type']}
╚═════════════════════════════════════════════════════════════╝
""")

    props = schema["properties"]
    print(f"  Properties ({len(props)}):")
    print(f"  {'logical_name':<45} {'type':<30} nullable")
    print("  " + "─" * 80)
    for p in props:
        print(
            f"  {p['logical_name']:<45} "
            f"{(p['type'] or ''):<30} "
            f"{'yes' if p['nullable'] else 'NO (required)'}"
        )

    nav = schema["nav_properties"]
    if nav:
        print(f"\n  Lookups / Nav Properties ({len(nav)}):")
        for n in nav:
            print(f"    → {n['name']:40s} {n['type']}")

    # MCP field hint
    logical_names = [p["logical_name"] for p in props]
    print(f"""
  ── MCP get_customer() $select hint ───────────────────────
  /api/data/v9.2/{schema['entity_set']}?$select={','.join(logical_names[:6])},...
""")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    xml = fetch_metadata("dataverse_metadata.xml")
    schema = parse_cr_aimodels(xml)
    print_schema(schema)

    with open("cr_aimodels_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print("[✓] Full schema → cr_aimodels_schema.json")
