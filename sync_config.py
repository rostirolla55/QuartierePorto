import os
import json
import re
from typing import Dict, Any, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Cartella che contiene i file page_config_*.json generati (con i soli percorsi dei frammenti).
INPUT_DIR = "text_files" 
# NUOVA COSTANTE: Directory base delle traduzioni
TRANSLATIONS_BASE_DIR = "data/translations"
# NUOVA COSTANTE: Nome del file di configurazione per lingua (ad esempio texts.json)
CONFIG_FILENAME = "texts.json"

# Eccezioni di Mapping: Mappa l'ID della pagina estratto dai frammenti al nome 
# del blocco da usare nel file di configurazione centrale (texts.json)
PAGE_ID_MAPPING_EXCEPTIONS = {
    # Risolve la discrepanza: se l'ID della pagina è 'index', il blocco di destinazione è 'home'.
    "index": "home", 
}

# Regex per estrarre la lingua (lang) e l'ID della pagina (page_id) 
# dalla struttura del file fragment, es: "it_manifattura_maintext1.html"
FILENAME_PATTERN = re.compile(r'(\w+)_(\w+)_maintext\d+\.html', re.IGNORECASE)

# Chiavi da sincronizzare/pulire (quelle che possono variare in numero)
DYNAMIC_KEYS_PREFIXES = ("mainText", "imageSource")
# Chiavi che devono essere preservate (metadati fissi)
# NOTA: Queste chiavi non verranno MAI eliminate dalla fase di pulizia dinamica.
STATIC_KEYS = (
    "pageTitle", "mainText", "playAudioButton", "pauseAudioButton", 
    "sourceText", "creationDate", "lastUpdate", "audioSource",
    "headImage" # CORREZIONE: Aggiunto 'headImage' per coerenza con la FASE 1 e garantire la sua preservazione.
)

# NUOVA CONFIGURAZIONE: Immagine di testata unica e percorso comune
DEFAULT_HEAD_IMAGE = 'public/images/panorama_bologna.jpg' 


def get_config_files(directory: str) -> list:
    """Trova tutti i file page_config_*.json nella directory specificata."""
    if not os.path.exists(directory):
        print(f"ERRORE: La cartella di input '{directory}' non esiste.")
        return []
    # NOTA: Il pattern di estrazione lang/page_id è gestito in 'sync_config'
    return [f for f in os.listdir(directory) if f.startswith("page_config_") and f.endswith(".json")]

def load_language_config(lang: str) -> Dict[str, Any]:
    """Carica la configurazione centrale (texts.json) per la lingua specificata."""
    filepath = os.path.join(TRANSLATIONS_BASE_DIR, lang, CONFIG_FILENAME)
    
    try:
        # Assicura che la cartella 'data/translations/xx' esista
        os.makedirs(os.path.dirname(filepath), exist_ok=True) 
        with open(filepath, 'r', encoding='utf-8') as f:
            print(f"  - Caricamento config lingua '{lang}' da: {filepath}")
            return json.load(f)
    except FileNotFoundError:
        print(f"  - ATTENZIONE: File config lingua '{lang}' non trovato. Verrà creato da zero.")
        return {}
    except json.JSONDecodeError:
        print(f"  - ERRORE: File config lingua '{lang}' non è un JSON valido. Inizializzazione fallita.")
        return {}
    except Exception as e:
        print(f"  - ERRORE inatteso durante il caricamento del config lingua '{lang}': {e}")
        return {}

def save_language_config(lang: str, data: Dict[str, Any]):
    """Salva la configurazione centrale aggiornata per la lingua specificata."""
    filepath = os.path.join(TRANSLATIONS_BASE_DIR, lang, CONFIG_FILENAME)
    
    try:
        # Assicura che la directory esista (già fatto nel load, ma meglio qui)
        os.makedirs(os.path.dirname(filepath), exist_ok=True) 
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"  ✅ SALVATAGGIO COMPLETO: Aggiornato config lingua '{lang}' in: {filepath}")
        
    except Exception as e:
        print(f"  ERRORE FATALE durante il salvataggio del file finale per '{lang}': {e}")


def extract_metadata_from_dynamic_config(config_data: Dict[str, Any]) -> Tuple[str, str] | None:
    """Estrae lingua e ID della pagina dai percorsi dei frammenti HTML."""
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
    print(json.dumps(stub, indent=4))
    print("\nSuggerimento: Correggi il processo che genera questo file e riprova la sincronizzazione.")


def sync_config(input_dir: str):
    """
    Sincronizza la configurazione centrale: pulisce le vecchie chiavi dinamiche
    e aggiorna con le nuove generate. Aggiunge le chiavi statiche mancanti.
    Gestisce i file texts.json separati per lingua nella struttura data/translations/xx/.
    """
    config_files = get_config_files(input_dir)
    if not config_files:
        print(f"ATTENZIONE: Nessun file 'page_config_*.json' trovato nella cartella '{input_dir}'. Nessun aggiornamento eseguito.")
        return

    print(f"Avvio sincronizzazione... Trovati {len(config_files)} file di configurazione da processare.")
    
    # Mappa per tenere traccia delle configurazioni per lingua modificate in memoria
    # Chiave: 'it', 'en', ecc. Valore: contenuto del rispettivo texts.json
    language_configs: Dict[str, Dict[str, Any]] = {}
    
    for filename in config_files:
        filepath = os.path.join(input_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                page_data_dynamic = json.load(f)
            
            metadata = extract_metadata_from_dynamic_config(page_data_dynamic)

            if metadata:
                lang, page_id = metadata
                
                # --- PUNTO CRITICO: APPLICAZIONE DEL MAPPING INDEX -> HOME ---
                target_key = PAGE_ID_MAPPING_EXCEPTIONS.get(page_id, page_id)

                # 1. Carica la configurazione della lingua se non è già in memoria
                if lang not in language_configs:
                    language_configs[lang] = load_language_config(lang)
                
                lang_config = language_configs[lang] # Riferimento al dict in memoria

                # 2. Assicura che la pagina (target_key) esista nel file di configurazione della lingua
                if target_key not in lang_config:
                    lang_config[target_key] = {}
                
                # Ottiene il blocco JSON esistente per questa pagina
                page_block = lang_config[target_key]

                print(f"\nProcessing: Pagina '{page_id}' (Target Block: '{target_key}') ({lang}) da '{filename}'")

                # --- FASE 1: GARANZIA DELLE CHIAVI STATICHE ---
                added_static_keys = []
                
                # 1. headImage (Immagine di Testata)
                if 'headImage' not in page_block:
                    page_block['headImage'] = DEFAULT_HEAD_IMAGE
                    added_static_keys.append('headImage')
                    
                # 2. audioSource
                if 'audioSource' not in page_block:
                    page_block['audioSource'] = f"Audio/{lang.lower()}/{target_key.lower()}.mp3"
                    added_static_keys.append('audioSource')

                if added_static_keys:
                    print(f"  - Aggiunte chiavi statiche (se mancanti): {', '.join(added_static_keys)}")
                    
                # --- FASE 2: PULIZIA DELLE VECCHIE CHIAVI DINAMICHE ---
                keys_to_delete = []
                for key in list(page_block.keys()): # Usiamo list() per iterare su una copia
                    # Se la chiave è dinamica (inizia con un prefisso e ha un suffisso numerico)
                    is_dynamic = any(key.startswith(prefix) and len(key) > len(prefix) for prefix in DYNAMIC_KEYS_PREFIXES)
                    
                    # E se questa chiave dinamica NON è presente nel nuovo set generato
                    # Poiché 'headImage' è in STATIC_KEYS, e non ha suffisso numerico, è già esclusa implicitamente dal controllo
                    # is_dynamic AND key not in page_data_dynamic.
                    if is_dynamic and key not in page_data_dynamic:
                        keys_to_delete.append(key)

                for key in keys_to_delete:
                    # Imposta la chiave a stringa vuota invece di eliminarla
                    page_block[key] = ""
                    print(f"  - PULIZIA: Impostata chiave dinamica a vuoto: '{key}'.")

                # --- FASE 3: AGGIORNAMENTO CON LE NUOVE CHIAVI DINAMICHE ---
                # Sovrascrive/Aggiunge i percorsi dei frammenti e delle immagini.
                page_block.update(page_data_dynamic)
                
                print(f"  - Aggiornamento dinamico completato.")

            else:
                print(f"  - SKIPPED: Impossibile estrarre lang/page_id da '{filename}'. Saltato.")

        except json.JSONDecodeError:
            print(f"  - ERRORE: File JSON non valido trovato: '{filename}'. Saltato.")
        except Exception as e:
            print(f"  - ERRORE inatteso durante l'elaborazione di '{filename}': {e}")

    # --- SALVATAGGIO DEL FILE FINALE SINCRONIZZATO PER OGNI LINGUA ---
    print("\nInizio fase di salvataggio per tutte le lingue processate...")
    for lang, config in language_configs.items():
        save_language_config(lang, config)

    print("\n✅ SINCRONIZZAZIONE GENERALE E SALVATAGGIO ESEGUITI.")


if __name__ == "__main__":
    # Esempio di utilizzo della funzione di sincronizzazione. 
    sync_config(INPUT_DIR)
    
    # Esempio di utilizzo della nuova funzione di debug
    # print_expected_stub(lang="it", page_id="chiesapioggia", num_fragments=3)