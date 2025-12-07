import os
import json
import re
from typing import Dict, Any, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Cartella di input relativa alla radice del progetto, dove si trovano i file page_config_*.json e i frammenti HTML.
INPUT_DIR = "OUTPUT_HTML" 

# Percorso BASE dove si trovano tutte le cartelle delle traduzioni.
# Lo script cercherà: BASE_TRANSLATIONS_PATH / [lang] / texts.json
BASE_TRANSLATIONS_PATH = "data/translations" 

# Regex per estrarre la lingua (lang) e l'ID della pagina (page_id) 
# es: "it_manifattura_maintext1.html"
FILENAME_PATTERN = re.compile(r'(\w+)_(\w+)_maintext\d+\.html', re.IGNORECASE)

# Lista COMPLETA delle chiavi dinamiche che devono ESISTERE in ogni blocco, anche se vuote.
ALL_DYNAMIC_KEYS = [
    "mainText1", "mainText2", "mainText3", "mainText4", "mainText5",
    "imageSource1", "imageSource2", "imageSource3", "imageSource4", "imageSource5"
]

def get_config_files(directory: str) -> list:
    """Trova tutti i file page_config_*.json nella directory specificata."""
    if not os.path.exists(directory):
        print(f"ERRORE: La cartella di input '{directory}' non esiste. Assicurati che il percorso sia corretto.")
        return []
    return [f for f in os.listdir(directory) if f.startswith("page_config_") and f.endswith(".json")]

def load_texts_json(lang: str) -> Tuple[str, Dict[str, Any]]:
    """Carica il file texts.json specifico per la lingua data."""
    # Costruisce il percorso completo del file texts.json, es: data/translations/it/texts.json
    filepath = os.path.join(BASE_TRANSLATIONS_PATH, lang, "texts.json")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return filepath, json.load(f)
    except FileNotFoundError:
        print(f"ATTENZIONE: File '{filepath}' non trovato. Verrà creato da zero/saltato se i dati non esistono.")
        return filepath, {}
    except json.JSONDecodeError:
        print(f"ERRORE: Il file '{filepath}' non è un JSON valido. Inizializzazione fallita.")
        return filepath, {}
    except Exception as e:
        print(f"ERRORE inatteso durante il caricamento del file '{filepath}': {e}")
        return filepath, {}

def save_texts_json(filepath: str, data: Dict[str, Any]):
    """Salva la configurazione aggiornata."""
    try:
        # Crea le directory se non esistono (es. data/translations/it)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"  - File aggiornato e salvato: {filepath}")
    except Exception as e:
        print(f"ERRORE FATALE durante il salvataggio del file {filepath}: {e}")

def extract_metadata_from_dynamic_config(config_data: Dict[str, Any]) -> Tuple[str, str] | None:
    """Estrae lingua e ID della pagina dai percorsi dei frammenti HTML."""
    for key, value in config_data.items():
        # Ci concentriamo sui mainTextX che hanno un percorso di file (stringa non vuota)
        if key.startswith("mainText") and len(key) > 8 and isinstance(value, str) and value.strip():
            match = FILENAME_PATTERN.search(value)
            if match:
                # Gruppo 1: lingua, Gruppo 2: page_id
                return match.group(1).lower(), match.group(2).lower()
    return None

def synchronize_config():
    """
    Sincronizza tutti i file texts.json per lingua con i frammenti generati.
    """
    
    # Dizionario per memorizzare i dati di configurazione caricati, organizzati per lingua.
    loaded_configs: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    
    config_files = get_config_files(INPUT_DIR)
    
    if not config_files:
        print(f"Nessun file di configurazione da processare. Esecuzione terminata.")
        return

    print(f"Trovati {len(config_files)} file di configurazione temporanei da sincronizzare...")

    for filename in config_files:
        filepath = os.path.join(INPUT_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                page_data_dynamic = json.load(f)
            
            metadata = extract_metadata_from_dynamic_config(page_data_dynamic)

            if not metadata:
                print(f"  - SKIPPED: Impossibile determinare lang/page_id da '{filename}'. Saltato.")
                continue

            lang, page_id = metadata
            
            # --- CARICAMENTO DEL FILE CENTRALE PER LA LINGUA (se non già caricato) ---
            if lang not in loaded_configs:
                path, data = load_texts_json(lang)
                loaded_configs[lang] = (path, data)
                if not data:
                    print(f"  - Non è stato possibile caricare o inizializzare '{lang}/texts.json'. Saltati gli aggiornamenti per questa lingua.")
                    continue
            
            central_filepath, central_data = loaded_configs[lang]

            if page_id not in central_data:
                print(f"  - ATTENZIONE: Pagina '{page_id}' non trovata in {lang}/texts.json. Creata una nuova entry vuota.")
                central_data[page_id] = {}
            
            page_block = central_data[page_id]
            
            print(f"\n-> Processazione: {lang}/{page_id} (da '{filename}')")
            
            # --- FASE 1: AZZERAMENTO DELLE CHIAVI DINAMICHE ---
            for key in ALL_DYNAMIC_KEYS:
                if key in page_block and page_block[key] != "":
                    print(f"  - Pulizia: Azzerata chiave '{key}'.")
                page_block[key] = ""
            
            # --- FASE 2: AGGIORNAMENTO CON LE NUOVE CHIAVI GENERATE ---
            page_block.update(page_data_dynamic)
            
            print(f"  - Sincronizzazione di '{page_id}' completata. Aggiornamento in memoria.")

        except json.JSONDecodeError:
            print(f"  - ERRORE: File JSON temporaneo '{filename}' non valido. Saltato.")
        except Exception as e:
            print(f"  - ERRORE inatteso durante l'elaborazione di '{filename}': {e}")

    # --- SALVATAGGIO DEI FILE CENTRALI AGGIORNATI ---
    print("\n==============================================")
    print("FASE DI SALVATAGGIO DEI FILE texts.json")
    print("==============================================")
    
    for lang, (filepath, data) in loaded_configs.items():
        if data:
            save_texts_json(filepath, data)
        else:
            print(f"  - SALTO: Nessun dato da salvare per la lingua '{lang}'.")

    print("\n✅ PROCESSO DI SINCRONIZZAZIONE A PERCORSI MULTIPLI COMPLETATO.")

if __name__ == "__main__":
    synchronize_config()