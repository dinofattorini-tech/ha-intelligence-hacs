"""Config flow per HA Intelligence."""
import voluptuous as vol
import aiohttp
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY, DEFAULT_BACKEND

class HAIntelligenceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key     = user_input[CONF_API_KEY].strip()
            backend_url = user_input.get("backend_url", DEFAULT_BACKEND).strip()
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{backend_url}/keys/validate",
                        headers={"X-API-Key": api_key},
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return self.async_create_entry(
                                title=f"HA Intelligence ({data.get('tier', 'free')})",
                                data={CONF_API_KEY: api_key, "backend_url": backend_url},
                            )
                        else:
                            errors[CONF_API_KEY] = "invalid_api_key"
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
                vol.Optional("backend_url", default=DEFAULT_BACKEND): str,
            }),
            errors=errors,
        )
