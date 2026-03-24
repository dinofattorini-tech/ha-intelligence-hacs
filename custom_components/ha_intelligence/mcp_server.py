#!/usr/bin/env python3
"""
HA Intelligence — MCP Server
Collega Claude Desktop a Home Assistant.

Configurazione in claude_desktop_config.json:
{
  "mcpServers": {
    "ha-intelligence": {
      "command": "python",
      "args": ["/percorso/a/mcp_server.py"],
      "env": {
        "HA_URL":     "http://homeassistant.local:8123",
        "HA_TOKEN":   "il-tuo-long-lived-access-token",
        "HAI_API_KEY":"hai_live_xxxxxxxxxxxx"
      }
    }
  }
}
"""

import asyncio, json, os
import aiohttp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

HA_URL      = os.getenv("HA_URL",      "http://homeassistant.local:8123")
HA_TOKEN    = os.getenv("HA_TOKEN",    "")
HAI_API_KEY = os.getenv("HAI_API_KEY", "")
BACKEND     = os.getenv("BACKEND_URL", "https://ha-intelligence-api-production.up.railway.app")

server = Server("ha-intelligence")
staging: dict = {}   # staging_views in memoria

# ── HTTP helpers ─────────────────────────────────────────────────
async def ha_get(path: str):
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{HA_URL}/api{path}", headers=headers) as r:
            return await r.json()

async def ha_post(path: str, data: dict):
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{HA_URL}/api{path}", headers=headers, json=data) as r:
            return await r.json()

async def track(tool: str, extra: dict = {}):
    try:
        headers = {"X-API-Key": HAI_API_KEY, "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND}/usage/track", headers=headers, json={"tool": tool, **extra})
    except Exception:
        pass  # il tracking non deve mai bloccare il tool

# ── TOOL DEFINITIONS ─────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_entities",
            description=(
                "Legge le entità di Home Assistant (luci, clima, sensori, switch, ecc.). "
                "Usa SEMPRE questo tool prima di creare qualsiasi vista Lovelace, "
                "per capire quali entità sono disponibili."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Filtra per dominio: light, climate, sensor, switch, cover, media_player… Lascia vuoto per tutto."
                    }
                }
            }
        ),
        types.Tool(
            name="write_lovelace_staging",
            description=(
                "Salva una vista Lovelace in staging (bozza). "
                "NON va in produzione finché l'utente non conferma con publish_lovelace. "
                "Usa questo tool dopo aver generato il YAML della vista."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "view_title": {"type": "string", "description": "Titolo della vista, es. 'Soggiorno'"},
                    "yaml_content": {"type": "string", "description": "YAML completo della vista Lovelace"},
                    "icon": {"type": "string", "description": "Icona MDI, es. 'mdi:sofa'"}
                },
                "required": ["view_title", "yaml_content"]
            }
        ),
        types.Tool(
            name="publish_lovelace",
            description=(
                "Pubblica la vista dallo staging in produzione su Home Assistant. "
                "Chiamare SOLO quando l'utente dice 'pubblica', 'ok vai', 'confermo'. "
                "Mostrare sempre il YAML all'utente prima di pubblicare."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "view_title": {"type": "string", "description": "Titolo della vista da pubblicare"}
                },
                "required": ["view_title"]
            }
        ),
        types.Tool(
            name="get_lovelace_config",
            description="Legge la configurazione Lovelace attuale di Home Assistant.",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]

# ── TOOL HANDLERS ────────────────────────────────────────────────
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    # ── get_entities ─────────────────────────────────────────────
    if name == "get_entities":
        try:
            states = await ha_get("/states")
            domain = arguments.get("domain", "")
            if domain:
                states = [e for e in states if e["entity_id"].startswith(domain + ".")]

            entities = [
                {
                    "entity_id":    e["entity_id"],
                    "friendly_name": e.get("attributes", {}).get("friendly_name", ""),
                    "state":        e["state"],
                    "domain":       e["entity_id"].split(".")[0],
                }
                for e in states[:300]
            ]
            await track("get_entities", {"count": len(entities)})
            return [types.TextContent(
                type="text",
                text=f"Trovate {len(entities)} entità{f' nel dominio {domain}' if domain else ''}:\n\n" +
                     json.dumps(entities, ensure_ascii=False, indent=2)
            )]
        except Exception as ex:
            return [types.TextContent(type="text", text=f"Errore: {ex}\nVerifica HA_URL e HA_TOKEN.")]

    # ── write_lovelace_staging ────────────────────────────────────
    elif name == "write_lovelace_staging":
        title   = arguments["view_title"]
        yaml_c  = arguments["yaml_content"]
        icon    = arguments.get("icon", "mdi:view-dashboard")
        staging[title] = {"title": title, "yaml": yaml_c, "icon": icon}
        await track("write_staging", {"view": title})
        return [types.TextContent(
            type="text",
            text=(
                f"✅ Vista '{title}' salvata in staging.\n\n"
                f"```yaml\n{yaml_c}\n```\n\n"
                "Scrivi **'pubblica'** per mandare in produzione su Home Assistant."
            )
        )]

    # ── publish_lovelace ──────────────────────────────────────────
    elif name == "publish_lovelace":
        title = arguments["view_title"]
        if title not in staging:
            return [types.TextContent(
                type="text",
                text=f"Nessuna vista '{title}' in staging. Prima genera la vista con write_lovelace_staging."
            )]
        try:
            import yaml
            current = await ha_get("/lovelace/config")
            views   = current.get("views", [])
            new_view = yaml.safe_load(staging[title]["yaml"]) or {}
            new_view["title"] = title
            new_view["icon"]  = staging[title]["icon"]

            replaced = False
            for i, v in enumerate(views):
                if v.get("title") == title:
                    views[i] = new_view; replaced = True; break
            if not replaced:
                views.append(new_view)

            current["views"] = views
            await ha_post("/lovelace/config", current)
            del staging[title]
            await track("publish_lovelace", {"view": title})
            return [types.TextContent(
                type="text",
                text=f"🚀 Vista '{title}' pubblicata su Home Assistant!\nApri il browser e la trovi nella barra di navigazione."
            )]
        except Exception as ex:
            return [types.TextContent(
                type="text",
                text=f"Errore pubblicazione: {ex}\nAssicurati che Lovelace sia in modalità storage (non YAML manuale)."
            )]

    # ── get_lovelace_config ───────────────────────────────────────
    elif name == "get_lovelace_config":
        try:
            cfg   = await ha_get("/lovelace/config")
            views = [{"title": v.get("title","?"), "path": v.get("path",""), "icon": v.get("icon","")} for v in cfg.get("views",[])]
            return [types.TextContent(
                type="text",
                text=f"Lovelace: {len(views)} viste\n\n" + json.dumps(views, ensure_ascii=False, indent=2)
            )]
        except Exception as ex:
            return [types.TextContent(type="text", text=f"Errore: {ex}")]

    return [types.TextContent(type="text", text=f"Tool '{name}' non riconosciuto.")]

# ── MAIN ─────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
