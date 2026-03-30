# config.py

# Algemene instellingen voor tests
CONFIG = {
    "base_url": "https://my.interoplab.eu",                 # 🌐 Basis-URL voor de applicatie
    "headless": True,                                      # 🐱‍👤 Test zichtbaar of niet
    "browser_name": "chromium",  # of "firefox", "webkit"   # 🦾 Browser type
    "storage_state_path": "utils/auth/state.json",               # 📂 Pad voor opslagstatus
    #"slow_mo": 3000,                                        # ⏳ Vertraging tussen acties in milliseconden
    "tracing_enabled": True,                                # 🔍 Tracing aan/uit
    "trace_output_path": "test-results/trace.zip",          # 📂 Pad voor trace-bestand
}
