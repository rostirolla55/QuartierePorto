import os
import json
import re
from typing import Dict, Any, Tuple

# --- CONFIGURAZIONE GLOBALE ---
# Cartella che contiene i file page_config_*.json generati (con i soli percorsi dei frammenti).
INPUT_DIR = "text_files" 
# Nome del file JSON centrale (texts.json) che VERRÀ AGGIORNATO.
CENTRAL_CONFIG_FILE = "texts.json" 

# Regex per estrarre la lingua (lang) e l'ID della pagina (page_id) 
# dalla struttura del file fragment, es: "it_manifattura_maintext1.html"
FILENAME_PATTERN = re.compile(r'(\w+)_(\w+)_maintext\d+\.html', re.IGNORECASE)

# Prefissi delle chiavi che possono essere generate dinamicamente e che devono essere pulite/aggiornate
DYNAMIC_KEYS_PREFIXES = ("mainText", "imageSource")


def load_central_config(filepath: str) -> Dict[str, Any]:
    """Carica la configurazione centrale esistente o ne crea una vuota se non esiste."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"Caricato file centrale esistente: '{filepath}'")
            return json.load(f)
    except FileNotFoundError:
        print(f"ATTENZIONE: Il file centrale '{filepath}' non è stato trovato. Verrà creato da zero.")
        return {}
    except json.JSONDecodeError:
        print(f"ERRORE: Il file centrale '{filepath}' non è un JSON valido. Inizializzazione fallita.")
        return {}

def save_central_config(filepath: str, data: Dict[str, Any]):
    """Salva la configurazione centrale aggiornata."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n✅ SINCRONIZZAZIONE COMPLETA E SALVATAGGIO ESEGUITI.")
        print(f"Il file centrale è stato aggiornato: '{filepath}'")
    except Exception as e:
        print(f"\nERRORE FATALE durante il salvataggio del file finale: {e}")

def extract_metadata_from_dynamic_config(config_data: Dict[str, Any]) -> Tuple[str, str] | None:
    """Estrae lingua e ID della pagina dai percorsi dei frammenti HTML."""
    # Cerchiamo la prima chiave mainTextX per estrarre i metadati
    for key, value in config_data.items():
        if key.startswith("mainText") and len(key) > len("mainText") and isinstance(value, str):
            match = FILENAME_PATTERN.search(value)
            if match:
                # Gruppo 1: lingua, Gruppo 2: page_id
                return match.group(1).lower(), match.group(2).lower()
    return None

def is_dynamic_key(key: str) -> bool:
    """Verifica se una chiave corrisponde al pattern dinamico (mainTextX, imageSourceX)."""
    # Controlla se la chiave inizia con uno dei prefissi E ha un numero dopo (es. mainText1)
    return any(key.startswith(prefix) and key[len(prefix):].isdigit() for prefix in DYNAMIC_KEYS_PREFIXES)


def sync_config(input_dir: str, central_config_file: str):
    """
    Sincronizza la configurazione centrale: pulisce le vecchie chiavi dinamiche
    e aggiorna con le nuove generate.
    """
    central_config = load_central_config(central_config_file)
    config_files = [f for f in os.listdir(input_dir) if f.startswith("page_config_") and f.endswith(".json")]
    
    if not config_files:
        print(f"ATTENZIONE: Nessun file 'page_config_*.json' trovato nella cartella '{input_dir}'. Nessun aggiornamento eseguito.")
        return

    print(f"\nInizio sincronizzazione di {len(config_files)} file...")

    for filename in config_files:
        filepath = os.path.join(input_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                page_data_dynamic = json.load(f)
            
            metadata = extract_metadata_from_dynamic_config(page_data_dynamic)

            if not metadata:
                print(f"  - SKIPPED: Impossibile estrarre lang/page_id da '{filename}'. Saltato. Assicurati che contenga chiavi come 'mainText1'.")
                continue

            lang, page_id = metadata
            
            # Verifichiamo se il file dinamico contiene dati utili per l'aggiornamento
            if not page_data_dynamic:
                print(f"  - ATTENZIONE: Il file '{filename}' è vuoto. Nessun aggiornamento per {page_id}/{lang}.")
                continue

            # --- PREPARAZIONE DEL BLOCCO CENTRALE ---
            if page_id not in central_config:
                print(f"  - CREAZIONE: Pagina '{page_id}' non trovata nel file centrale. Creata nuova entry vuota.")
                central_config[page_id] = {} 

            page_block = central_config[page_id]

            print(f"\n--- Processando {page_id.upper()} ({lang.upper()}) ---")
            
            # --- FASE 1: PULIZIA DELLE VECCHIE CHIAVI DINAMICHE ---
            keys_to_delete = []
            
            # Itera sulle chiavi attuali del blocco centrale
            for key in list(page_block.keys()): # Usiamo list() per iterare su una copia mentre modifichiamo l'originale
                if is_dynamic_key(key):
                    # Se la chiave è dinamica E NON è presente nel nuovo set generato
                    if key not in page_data_dynamic:
                        keys_to_delete.append(key)
                        del page_block[key] # Eliminazione immediata

            if keys_to_delete:
                print(f"  - PULIZIA: Eliminate {len(keys_to_delete)} chiavi dinamiche obsolete: {keys_to_delete}")
            else:
                print("  - PULIZIA: Nessuna chiave dinamica obsoleta trovata o eliminata.")

            # --- FASE 2: AGGIORNAMENTO CON LE NUOVE CHIAVI DINAMICHE ---
            keys_updated = 0
            for key, value in page_data_dynamic.items():
                if is_dynamic_key(key):
                    page_block[key] = value
                    keys_updated += 1

            if keys_updated > 0:
                 print(f"  - AGGIORNAMENTO: Aggiunte/Aggiornate {keys_updated} chiavi dinamiche dal file '{filename}'.")
            else:
                print("  - AGGIORNAMENTO: Nessuna chiave dinamica aggiunta (verifica che il file di input non sia vuoto).")

            print(f"--- Fine elaborazione {page_id.upper()} ---\n")

        except json.JSONDecodeError:
            print(f"  - ERRORE: File JSON non valido trovato: '{filename}'. Saltato.")
        except Exception as e:
            print(f"  - ERRORE inatteso durante l'elaborazione di '{filename}': {e}")

    # --- SALVATAGGIO DEL FILE FINALE SINCRONIZZATO ---
    save_central_config(central_config_file, central_config)

if __name__ == "__main__":
    sync_config(INPUT_DIR, CENTRAL_CONFIG_FILE)