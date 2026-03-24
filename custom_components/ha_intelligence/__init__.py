"""
HA Intelligence Integration.
Verificato per Home Assistant 2026.1+.
"""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)
DOMAIN = "ha_intelligence"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Configura l'integrazione dopo che l'utente ha completato il Config Flow.
    """
    _LOGGER.info("Inizializzazione di HA Intelligence...")

    # Memorizziamo i dati dell'entry (come l'API Key) in un posto sicuro
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Qui potremmo aggiungere logica futura per testare la connessione al backend Railway
    # Se il test fallisce, restituirebbe: raise ConfigEntryNotReady

    _LOGGER.info("HA Intelligence pronto. API Key registrata correttamente.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Gestisce la rimozione pulita dell'integrazione.
    """
    _LOGGER.info("Rimozione dell'integrazione HA Intelligence.")
    
    # Rimuove i dati dalla memoria
    if entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)

    return True