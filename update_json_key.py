import sys
import os
import json

# --- CONFIGURAZIONE ---
JSON_BASE_PATH = "data/translations"
LANGUAGES = ['it', 'en', 'es', 'fr']

def update_json_key(lang_code, full_key, new_value):
    """
    Aggiorna il valore di una chiave annidata (es. paginaxy.mainText1) in un file JSON di traduzione.
    """
    if lang_code not in LANGUAGES:
        print(f"ERRORE: Codice lingua '{lang_code}' non valido. Deve essere tra {LANGUAGES}.")
        return False
        
    try:
        # La chiave è nel formato 'page_id.key_name'
        page_id, key_name = full_key.split('.', 1)
    except ValueError:
        print(f"ERRORE: Chiave non valida. Formato atteso: 'page_id.key'. Ricevuto: '{full_key}'")
        return False

    json_path = os.path.join(JSON_BASE_PATH, lang_code, "texts.json")
    
    if not os.path.exists(json_path):
        print(f"ERRORE: File JSON non trovato per la lingua '{lang_code}' in: {json_path}")
        return False
        
    print(f"-> Aggiornamento di {lang_code}/texts.json per la chiave {full_key}...")

    try:
        # Legge il file JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Verifica se l'ID della pagina esiste nel JSON
        if page_id not in data:
            print(f"ERRORE: ID pagina '{page_id}' non trovato nel file JSON.")
            return False
            
        # Aggiorna la chiave specifica all'interno del blocco della pagina
        data[page_id][key_name] = new_value
        
        # Scrive il file JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ Aggiornato con successo: '{full_key}' = '{new_value}' in lingua '{lang_code}'.")
        return True

    except Exception as e:
        print(f"ERRORE durante l'operazione su texts.json: {e}")
        return False

# --- Entry Point ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("USO: python update_json_key.py <codice_lingua> <id_pagina.chiave> <nuovo_valore>")
        print("Esempio: python update_json_key.py it paginaxy.mainText1 it_paginaxy_maintext_1.html")
        sys.exit(1)
        
    lang_code = sys.argv[1].lower()
    full_key = sys.argv[2]
    new_value = sys.argv[3]
    
    if not update_json_key(lang_code, full_key, new_value):
        sys.exit(1)
    
    sys.exit(0)