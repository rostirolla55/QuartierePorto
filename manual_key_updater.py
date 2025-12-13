import json
import os
import sys
from typing import Dict, Any

# Definizioni dei percorsi
# Directory base che contiene le cartelle delle lingue (es. 'it', 'en')
BASE_TRANSLATION_DIR = os.path.join('data', 'translations') 
MANUAL_KEYS_FILE = 'manual_keys_template.json'  # File di override (nella root)
TEXTS_FILENAME = 'texts.json' # Nome del file di traduzione all'interno di ogni cartella lingua
PAGE_ID_ARG_INDEX = 1 # L'ID della pagina è il primo argomento dopo il nome dello script

def load_json(filepath: str) -> Dict[str, Any] | None:
    """Carica un file JSON con gestione degli errori."""
    if not os.path.exists(filepath):
        # NOTA: Se il file texts.json non esiste nel percorso specifico della lingua,
        # lo inizializziamo con un dizionario vuoto per permettere l'aggiunta.
        if filepath.endswith(TEXTS_FILENAME):
            return {}
        print(f"ERRORE: File '{filepath}' non trovato. Interruzione.")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERRORE: Impossibile decodificare il JSON da '{filepath}': {e}")
        return None
    except Exception as e:
        print(f"ERRORE inatteso durante il caricamento di '{filepath}': {e}")
        return None

def save_json(filepath: str, data: Dict[str, Any]):
    """Salva il file JSON con gestione degli errori."""
    try:
        # Crea la directory se non esiste (es. 'data/translations/it')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ File '{filepath}' salvato con successo.")
    except Exception as e:
        print(f"ERRORE: Impossibile salvare '{filepath}': {e}")

def main():
    """
    Funzione principale. Applica gli override manuali per la PAGE_ID passata, 
    cercando texts.json nel percorso specifico per lingua.
    """
    if len(sys.argv) < 2:
        print("ERRORE: ID della pagina non specificato.")
        print("Uso: python manual_key_updater.py <PAGE_ID>")
        sys.exit(1)

    page_id = sys.argv[PAGE_ID_ARG_INDEX].lower()
    print(f"Avvio aggiornamento manuale per la pagina: {page_id}")
    
    # 1. Carica manual_keys_template.json (la sorgente degli override - dalla root)
    manual_data = load_json(MANUAL_KEYS_FILE)
    if manual_data is None:
        sys.exit(1) 

    # 2. Trova il blocco di override per la pagina corrente
    page_overrides = manual_data.get(page_id)
    if not page_overrides:
        print(f"AVVISO: Nessun override manuale trovato in '{MANUAL_KEYS_FILE}' per la pagina '{page_id}'. Nessuna azione eseguita.")
        sys.exit(0)
    
    global_modified = False
    
    # 3. Itera su tutte le lingue definite negli override per la pagina corrente
    for lang, overrides in page_overrides.items():
        lang = lang.lower() # Assicura che la lingua sia minuscola per il path
        
        # 3a. Costruisci il percorso del file texts.json specifico per lingua
        # Esempio: data/translations/it/texts.json
        lang_texts_path = os.path.join(BASE_TRANSLATION_DIR, lang, TEXTS_FILENAME)
        
        print(f"\nProcessing lingua '{lang}' | Target file: {lang_texts_path}")
        
        # 3b. Carica il file texts.json specifico (Target). 
        texts_data = load_json(lang_texts_path)
        if texts_data is None:
            print(f"AVVISO: Impossibile caricare o inizializzare '{lang_texts_path}'. Saltato.")
            continue

        # 3c. Assicurati che la pagina esista nel file texts.json (specifico per lingua)
        if page_id not in texts_data:
            print(f"AVVISO: La pagina '{page_id}' non esiste in '{lang_texts_path}'. Aggiungo il nodo.")
            texts_data[page_id] = {}
        
        # 3d. Applica gli override
        page_data = texts_data[page_id]
        applied_keys = []
        modified = False

        for key, value in overrides.items():
            # Applica l'override se la chiave non esiste o se il valore è diverso
            if page_data.get(key) != value:
                page_data[key] = value
                applied_keys.append(key)
                modified = True
                global_modified = True
        
        # 3e. Salva il file texts.json specifico per lingua se ci sono state modifiche
        if modified:
            save_json(lang_texts_path, texts_data)
            print(f"  - Override applicati per '{lang}': {', '.join(applied_keys)}")
        else:
            print(f"  - Nessuna modifica da applicare in '{lang_texts_path}' per la pagina '{page_id}'.")


    if global_modified:
        print(f"\n🎉 Aggiornamento manuale COMPLETATO. Almeno un file texts.json è stato modificato.")
    else:
        print("\nAVVISO: Nessuna modifica applicata su nessun file texts.json.")


if __name__ == "__main__":
    main()