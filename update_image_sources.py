import sys
import os
import json

# --- CONFIGURAZIONE ---
JSON_BASE_PATH = "data/translations"
IMAGE_LIST_FILE = "image_list.txt"
LANGUAGES = ['it', 'en', 'es', 'fr']

def update_image_sources_from_list(page_id):
    """
    Legge la lista delle immagini (image_list.txt) e aggiorna le chiavi imageSourceX 
    nel JSON per una specifica pagina e per tutte le lingue.
    """
    # Determina il percorso dello script in esecuzione per trovare image_list.txt
    script_dir = os.path.dirname(os.path.abspath(__file__))
    image_list_path = os.path.join(script_dir, IMAGE_LIST_FILE)

    if not os.path.exists(image_list_path):
        print(f"ERRORE: File di lista immagini non trovato: {image_list_path}")
        return False

    updates = {}
    try:
        # Legge il file di lista immagini
        with open(image_list_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue # Salta commenti e righe vuote
                
                parts = line.split('|')
                if len(parts) == 3:
                    list_page_id, key_name, image_path = [p.strip() for p in parts]
                    
                    if list_page_id == page_id:
                        # Raccoglie tutti gli aggiornamenti per la pagina corrente
                        updates[key_name] = image_path
                else:
                    print(f"AVVISO: Riga non valida nel file {IMAGE_LIST_FILE}: {line}")

    except Exception as e:
        print(f"ERRORE durante la lettura di {IMAGE_LIST_FILE}: {e}")
        return False

    if not updates:
        print(f"AVVISO: Nessuna immagine trovata per la pagina '{page_id}' nel file di lista. Continuo.")
        return True 

    # Inizia l'aggiornamento dei file JSON per ogni lingua
    success = True
    for lang_code in LANGUAGES:
        # Costruisce il percorso del file JSON (es. data/translations/it/texts.json)
        json_path = os.path.join(JSON_BASE_PATH, lang_code, "texts.json")
        
        # NOTE: Si assume che i percorsi BASE_PATH_IMAGES e BASE_PATH_TEXT_FILES
        # siano definiti in main.js e non qui. Qui salviamo solo il percorso relativo.

        if not os.path.exists(json_path):
            print(f"AVVISO: File JSON non trovato per la lingua '{lang_code}' in: {json_path}. Saltato.")
            continue
            
        print(f"-> Aggiornamento immagini in {lang_code}/texts.json per la pagina {page_id}...")

        try:
            # Legge il file JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if page_id in data:
                # Applica gli aggiornamenti
                for key, value in updates.items():
                    data[page_id][key] = value
                
                # Scrive il file JSON
                with open(json_path, 'w', encoding='utf-8') as f:
                    # ensure_ascii=False per preservare i caratteri UTF-8
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
                print(f"✅ Immagini aggiornate con successo nel JSON '{lang_code}'.")
            else:
                print(f"ERRORE: ID pagina '{page_id}' non trovato nel file JSON '{lang_code}'.")
                success = False
        
        except Exception as e:
            print(f"ERRORE durante la scrittura su texts.json ({lang_code}): {e}")
            success = False
            
    return success

# --- Entry Point ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USO: python update_image_sources.py <id_pagina>")
        print("Esempio: python update_image_sources.py pittoricarracci")
        sys.exit(1)
        
    page_id = sys.argv[1]
    
    if not update_image_sources_from_list(page_id):
        sys.exit(1)
    
    sys.exit(0)