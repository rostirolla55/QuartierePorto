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

# NUOVO: Regex per estrarre la lingua e l'ID della pagina dal nome del file JSON di configurazione temporanea
CONFIG_FILENAME_PATTERN = re.compile(r'page_config_(\w+)_(\w+)\.json', re.IGNORECASE)

# Chiavi da sincronizzare/pulire (quelle che possono variare in numero)
DYNAMIC_KEYS_PREFIXES = ("mainText", "imageSource")
# Chiavi che devono essere preservate (metadati fissi)
STATIC_KEYS = (
    "pageTitle", "mainText", "playAudioButton", "pauseAudioButton", 
    "sourceText", "creationDate", "lastUpdate", "audioSource"
)


def get_config_files(directory: str) -> list:
    """Trova tutti i file page_config_*.json nella directory specificata."""
    if not os.path.exists(directory):
        print(f"ERRORE: La cartella di input '{directory}' non esiste.")
        return []
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

def save_central_config(filepath: str, data: Dict[str, Any]):
    """Salva la configurazione centrale aggiornata."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ SINCRONIZZAZIONE COMPLETA E SALVATAGGIO ESEGUITI.")
        print(f"Il file centrale è stato aggiornato: '{filepath}'")
        
    except Exception as e:
        print(f"\nERRORE FATALE durante il salvataggio del file finale: {e}")


def extract_metadata_from_config_filename(filename: str) -> Tuple[str, str] | None:
    """
    Estrae lingua e ID della pagina dal nome del file di configurazione temporanea (page_config_<lang>_<page_id>.json).
    Questa è la strategia preferita.
    """
    match = CONFIG_FILENAME_PATTERN.search(filename)
    if match:
        # Gruppo 1: lingua, Gruppo 2: page_id
        return match.group(1).lower(), match.group(2).lower()
    return None

def extract_metadata_from_dynamic_config(config_data: Dict[str, Any]) -> Tuple[str, str] | None:
    """
    (FALLBACK) Estrae lingua e ID della pagina dai percorsi dei frammenti HTML
    (es. it_manifattura_maintext1.html).
    """
    for key, value in config_data.items():
        if key.startswith("mainText") and isinstance(value, str):
            match = FILENAME_PATTERN.search(value)
            if match:
                # Gruppo 1: lingua, Gruppo 2: page_id
                return match.group(1).lower(), match.group(2).lower()
    return None

def print_expected_stub(lang: str, page_id: str, num_fragments: int = 1):
    """
    Stampa uno stub JSON di esempio basato su lang e page_id per aiutare il debug.
    Questo JSON è il contenuto atteso del file page_config_*.json mancante.
    """
    print("\n" + "="*50)
    print(f"STRUTTURA PREVISTA PER IL FILE CONFIG MANCANTE ({lang.upper()}/{page_id.upper()})")
    print("="*50)
    
    stub = {}
    for i in range(1, num_fragments + 1):
        html_fragment_name = f"{lang.lower()}_{page_id.lower()}_maintext{i}.html"
        stub[f"mainText{i}"] = html_fragment_name
        stub[f"imageSource{i}"] = "" 

    expected_filename = f"page_config_{lang.lower()}_{page_id.lower()}.json"

    print(f"Il file JSON di configurazione temporanea atteso sarebbe '{expected_filename}'.")
    print(f"Dovrebbe essere salvato nella cartella '{INPUT_DIR}' con il seguente contenuto:")
    print(json.dumps(stub, indent=4, ensure_ascii=False))
    print("\nSuggerimento: Correggi il processo che genera questo file e riprova la sincronizzazione.")


def sync_config(input_dir: str, central_config_file: str):
    """
    Sincronizza la configurazione centrale: pulisce le vecchie chiavi dinamiche
    e aggiorna con le nuove generate.
    """
    central_config = load_central_config(central_config_file)
    config_files = get_config_files(input_dir)
    
    if not config_files:
        print(f"ATTENZIONE: Nessun file 'page_config_*.json' trovato nella cartella '{input_dir}'. Nessun aggiornamento eseguito.")
        return

    print(f"Trovati {len(config_files)} file di configurazione da sincronizzare...")

    for filename in config_files:
        filepath = os.path.join(input_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                page_data_dynamic = json.load(f)
            
            # --- STRATEGIA DI ESTRAZIONE METADATI ---
            # 1. Tentativo di estrazione dal nome del file (PIÙ AFFIDABILE)
            metadata = extract_metadata_from_config_filename(filename) 
            
            if not metadata:
                # 2. Fallback: Tentativo di estrazione dal contenuto del file (MENO AFFIDABILE)
                metadata = extract_metadata_from_dynamic_config(page_data_dynamic)
            # ----------------------------------------

            if metadata:
                lang, page_id = metadata
                
                # Usa page_id come chiave principale, adattandosi alla struttura piatta dell'utente.
                
                # Assicura che la struttura di base esista nel file centrale
                if page_id not in central_config:
                    # Questo avviso apparirà solo se la pagina è stata processata per la prima volta
                    # o se il metadato è stato perso
                    print(f"  - ATTENZIONE: Pagina '{page_id}' non trovata nel file centrale. Creata una nuova entry vuota.")
                    central_config[page_id] = {} 

                # Ottiene il blocco JSON esistente per questa pagina
                page_block = central_config[page_id]

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
                # Nota: Le chiavi STATICHE presenti in page_block (es. pageTitle, audioSource)
                # non vengono toccate da questo update, a meno che page_data_dynamic 
                # non contenga chiavi STATICHE (il che non dovrebbe accadere se i file page_config_* # contengono solo riferimenti a frammenti come da tua descrizione iniziale).
                page_block.update(page_data_dynamic)
                
                print(f"  - Sincronizzata pagina '{page_id}' ({lang}).")

            else:
                print(f"  - SKIPPED: Impossibile estrarre lang/page_id da '{filename}'. Saltato.")
                print(f"    (Controllare se il nome del file JSON è nel formato page_config_<lang>_<page_id>.json)")


        except json.JSONDecodeError:
            print(f"  - ERRORE: File JSON non valido trovato: '{filename}'. Saltato.")
        except Exception as e:
            print(f"  - ERRORE inatteso durante l'elaborazione di '{filename}': {e}")

    # --- SALVATAGGIO DEL FILE FINALE SINCRONIZZATO ---
    save_central_config(central_config_file, central_config)

if __name__ == "__main__":
    # Esempio di utilizzo della funzione di sincronizzazione
    sync_config(INPUT_DIR, CENTRAL_CONFIG_FILE)
    
    # Esempio di utilizzo della nuova funzione di debug
    # Esegue il debug per chiesapioggia con 3 frammenti
    print_expected_stub(lang="it", page_id="chiesapioggia", num_fragments=3)