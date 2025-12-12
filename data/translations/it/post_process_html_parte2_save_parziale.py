import os
import json # Assicurati che json sia importato, anche se non mostrato nel frammento originale

# Assumiamo che OUTPUT_DIR sia definito altrove
try:
    OUTPUT_DIR
except NameError:
    OUTPUT_DIR = "text_files"

def save_results(fragments: dict, config_data: dict, page_id: str, lang: str):
    """Salva i frammenti HTML e il file JSON di configurazione temporanea."""
    
    # --- NUOVA LOGICA DI SANIFICAZIONE (Problema 2) ---
    # Convertiamo i percorsi delle immagini in minuscolo per evitare problemi di case-sensitivity 
    # nei file system e nei server web.
    sanitized_config_data = {}
    for key, value in config_data.items():
        # Regola 1: Se la chiave è un percorso immagine e il valore è una stringa...
        if key.startswith("imageSource") and isinstance(value, str):
            sanitized_config_data[key] = value.lower()
        # Regola 2: Mantieni tutti gli altri dati invariati
        else:
            sanitized_config_data[key] = value
            
    config_data = sanitized_config_data
    # --------------------------------------------------
    
    # Costruisce il nome del file JSON includendo la lingua, come richiesto
    json_filename = f"page_config_{lang}_{page_id}.json" # <--- UTILIZZA lang QUI

    json_filepath = os.path.join(OUTPUT_DIR, json_filename)
    
    # 1. Salva il JSON di configurazione
    try:
        # Usa il config_data sanificato
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        print(f"Creato file di configurazione: {json_filepath}")
    except Exception as e:
        print(f"ERRORE nel salvataggio del JSON: {e}")
        return

    # 2. Salva i frammenti HTML
    # ... (il codice per salvare i file .html in OUTPUT_DIR)
    for filename, html_content in fragments.items():
        html_filepath = os.path.join(OUTPUT_DIR, filename)
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Creato file frammento: {html_filepath}")

    print(f"Sincronizzazione frammenti per {lang}/{page_id} completata.")

# ... resto delle funzioni