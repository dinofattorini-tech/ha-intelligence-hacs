"""Config flow per HA Intelligence."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

DOMAIN = "ha_intelligence"

class HAIntelligenceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il config flow per HA Intelligence."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Gestisce il primo passo quando l'utente aggiunge l'integrazione."""
        errors = {}

        if user_input is not None:
            # Qui potremmo validare la chiave (es. se inizia con 'hai_live_')
            api_key = user_input.get("api_key")
            
            if not api_key.startswith("hai_live_"):
                errors["base"] = "invalid_api_key"
            else:
                return self.async_create_entry(
                    title="HA Intelligence", 
                    data=user_input
                )

        # Form che appare all'utente
        data_schema = vol.Schema({
            vol.Required("api_key"): str,
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema, 
            errors=errors
        )