# ⚡ HA Intelligence
### Design Home Assistant Dashboards with the Power of Claude AI

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![HA Version](https://img.shields.io/badge/HA-2024.1%2B-green.svg)](https://www.home-assistant.io/)

HA Intelligence turns **Claude Desktop** into an architect for your home. It reads your real-world entities and creates professional Lovelace views using natural language. No YAML knowledge required.

---

## 🚀 Quick Setup (10 Minutes)

### 1. Get your API Key
Register at [ha-intelligence.netlify.app](https://ha-intelligence.netlify.app/login.html) to obtain your unique API key (`hai_live_xxxxxxxxxxxxx`).

### 2. Install the Integration on Home Assistant
1. Open **HACS** → **Integrations** → **Explore & Download**.
2. Search for **"HA Intelligence"** (or add this GitHub URL as a Custom Repository).
3. Click Install and **restart Home Assistant**.
4. Go to **Settings → Devices & Services → Add Integration**, search for "HA Intelligence," and paste your **API Key**.

### 3. Configure Claude Desktop
You must manually locate or create your `claude_desktop_config.json` file. Common locations include:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Paste the following configuration (replace placeholders with your data):

```json
{
  "mcpServers": {
    "ha-intelligence": {
      "command": "python",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "HA_URL": "[http://homeassistant.local:8123](http://homeassistant.local:8123)",
        "HA_TOKEN": "YOUR_LONG_LIVED_ACCESS_TOKEN",
        "HAI_API_KEY": "hai_live_xxxxxxxxxxxx"
      }
    }
  }
}
