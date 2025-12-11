import os
import json
import re
from typing import Dict, Any, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Cartella che contiene i file page_config_*.json generati (con i soli percorsi dei frammenti).
INPUT_DIR = "output_html_fragments" 
# Nome del file JSON centrale (texts.json) che VERRÀ AGGIORNATO.
CENTRAL_CONFIG_FILE = "texts.json" 

# Regex per estrarre la lingua (lang) e l'ID della pagina (page_id) 
# dalla struttura del file fragment, es: "it_manifattura_maintext1.html"
FILENAME_PATTERN = re.compile(r'(\w+)_(\w+)_maintext\d+\.html', re.IGNORECASE)

# Chiavi da sincronizzare/pulire (quelle che possono variare in numero)
DYNAMIC_KEYS_PREFIXES = ("mainText", "imageSource")
# Chiavi che devono essere preservate (metadati fissi)
STATIC_KEYS = (
    "pageTitle", "mainText", "playAudioButton", "pauseAudioButton", 
    "sourceText", "creationDate", "lastUpdate", "audioSource"
)


def get_config_files(directory: str) -> list:
    """Trova tutti i file page_config_*.json nella directory specificata."""
    return [f for f in os.listdir(directory) if f.startswith("page_config_") and f.endswith(".json")]

def load_central_config(filepath: str) -> Dict[str, Any]:
    """Carica la configurazione centrale esistente o ne crea una vuota se non esiste."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ATTENZIONE: Il file centrale '{filepath}' non è stato trovato. Verrà creato da zero.")
        print("ATTENZIONE: Senza una struttura precompilata, le chiavi statiche saranno mancanti.")
        return {}
    except json.JSONDecodeError:
        print(f"ERRORE: Il file centrale '{filepath}' non è un JSON valido. Inizializzazione fallita.")
        return {}
    except Exception as e:
        print(f"ERRORE inatteso durante il caricamento del file centrale: {e}")
        return {}

def extract_metadata_from_dynamic_config(config_data: Dict[str, Any]) -> Tuple[str, str] | None:
    """Estrae lingua e ID della pagina dai percorsi dei frammenti HTML."""
    for key, value in config_data.items():
        if key.startswith("mainText") and isinstance(value, str):
            match = FILENAME_PATTERN.search(value)
            if match:
                return match.group(1).lower(), match.group(2).lower()
    return None

def sync_config(input_dir: str, central_config_file: str):
    """
    Sincronizza la configurazione centrale: pulisce le vecchie chiavi dinamiche
    e aggiorna con le nuove generate.
    """
    central_config = load_central_config(central_config_file)
    config_files = get_config_files(input_dir)
    
    if not config_files:
        print(f"ATTENZIONE: Nessun file 'page_config_*.json' trovato. Nessun aggiornamento eseguito.")
        return

    print(f"Trovati {len(config_files)} file di configurazione da sincronizzare...")

    for filename in config_files:
        filepath = os.path.join(input_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                page_data_dynamic = json.load(f)
            
            metadata = extract_metadata_from_dynamic_config(page_data_dynamic)

            if metadata:
                lang, page_id = metadata
                
                # Assicura che la struttura di base esista nel file centrale
                if lang not in central_config:
                    central_config[lang] = {}
                if page_id not in central_config[lang]:
                    print(f"  - ATTENZIONE: Pagina '{page_id}' non trovata nel file centrale. Creata una nuova entry vuota.")
                    central_config[lang][page_id] = {}
                
                # Ottiene il blocco JSON esistente per questa pagina
                page_block = central_config[lang][page_id]

                # --- FASE 1: PULIZIA DELLE VECCHIE CHIAVI DINAMICHE ---
                keys_to_delete = []
                for key in page_block.keys():
                    # Se la chiave è dinamica (inizia per mainText o imageSource)
                    is_dynamic = any(key.startswith(prefix) and len(key) > len(prefix) for prefix in DYNAMIC_KEYS_PREFIXES)
                    
                    # E se questa chiave dinamica NON è presente nel nuovo set generato
                    if is_dynamic and key not in page_data_dynamic:
                        keys_to_delete.append(key)

                for key in keys_to_delete:
                    del page_block[key]
                    print(f"  - PULIZIA: Eliminata vecchia chiave '{key}' per {page_id}/{lang}.")

                # --- FASE 2: AGGIORNAMENTO CON LE NUOVE CHIAVI DINAMICHE ---
                # Aggiunge/aggiorna solo i nuovi percorsi dei frammenti e delle immagini.
                page_block.update(page_data_dynamic)
                
                print(f"  - Sincronizzata pagina '{page_id}' ({lang}).")

            else:
                print(f"  - SKIPPED: Impossibile estrarre lang/page_id da '{filename}'. Saltato.")

        except json.JSONDecodeError:
            print(f"  - ERRORE: File JSON non valido trovato: '{filename}'. Saltato.")
        except Exception as e:
            print(f"  - ERRORE inatteso durante l'elaborazione di '{filename}': {e}")

    # --- SALVATAGGIO DEL FILE FINALE SINCRONIZZATO ---
    try:
        with open(central_config_file, 'w', encoding='utf-8') as f:
            json.dump(central_config, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ SINCRONIZZAZIONE COMPLETA E SALVATAGGIO ESEGUITI.")
        print(f"Il file centrale è stato aggiornato: '{central_config_file}'")
        
    except Exception as e:
        print(f"\nERRORE FATALE durante il salvataggio del file finale: {e}")

if __name__ == "__main__":
    sync_config(INPUT_DIR, CENTRAL_CONFIG_FILE)