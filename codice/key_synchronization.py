import json
import os
import re
from typing import Dict, Any

# Definizioni dei percorsi
TEXTS_FILE = 'texts.json'
# CORREZIONE: Imposta la directory di configurazione temporanea a 'text_files'
CONFIG_DIR = 'text_files' 

# NUOVA CONFIGURAZIONE: Immagine di testata unica e percorso comune
# L'immagine deve esistere in 'public/images/panorama_bologna.jpg'
DEFAULT_HEAD_IMAGE = 'public/images/panorama_bologna.jpg' 

# Pattern Regex Corretto: Cerca page_config_ seguita da lang e page_id
# Esempio atteso: page_config_it_manifattura.json
FILENAME_PATTERN = re.compile(r'page_config_([a-z]{2})_([a-z0-9]+)\.json$', re.IGNORECASE)

def load_json(filepath: str) -> Dict[str, Any] | None:
    """Carica un file JSON con gestione degli errori."""
    if not os.path.exists(filepath):
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

def update_texts_json(page_id: str, lang: str, config_data: Dict[str, Any]):
    """
    Aggiorna il file texts.json con le chiavi dinamiche dal file di configurazione
    e assegna 'headImage' e 'audioSource' se non sono già definite.
    Accetta config_data direttamente come parametro.
    """
    
    # 2. Carica il file texts.json esistente
    texts_data = load_json(TEXTS_FILE) or {}

    # Assicurati che la struttura esista
    if page_id not in texts_data:
        texts_data[page_id] = {}
        
    page_data_lang = texts_data[page_id].get(lang, {})
    new_page_data = page_data_lang.copy()
    added_keys = []
    
    print(f"Aggiornamento delle chiavi per pagina: {page_id}, lingua: {lang}...")
    
    # --- LOGICA IMMAGINE DI TESTATA (headImage) - SEMPLIFICATA ---
    # Assegna il percorso comune se la chiave non esiste ancora.
    if 'headImage' not in new_page_data:
        new_page_data['headImage'] = DEFAULT_HEAD_IMAGE
        added_keys.append('headImage')
    # ---------------------------------------------

    # 3. Chiavi di base statiche
    # Il pageTitle viene preso da config_data (generato da sync_config?) se è presente
    if 'pageTitle' in config_data:
        new_page_data['pageTitle'] = config_data.get('pageTitle')
    
    if 'audioSource' not in new_page_data:
        # Aggiunge l'audioSource se non esiste.
        new_page_data['audioSource'] = f"Audio/{lang.lower()}/{page_id.lower()}.mp3"
        added_keys.append('audioSource')

    # 4. Chiavi dinamiche (Testo e Immagini estratte dal DOCX)
    # Vengono incluse così come sono.
    for key, value in config_data.items():
        # Verifichiamo se la chiave è di tipo 'mainTextX' o 'imageSourceX'
        # Ignoriamo pageTitle se è già stato gestito (anche se .update() lo gestisce)
        if key.startswith('mainText') or key.startswith('imageSource'):
            # Il check 'key not in new_page_data or new_page_data[key] != value' non è più 
            # strettamente necessario se usiamo update, ma lo manteniamo per tracking
            if key not in new_page_data or new_page_data[key] != value:
                new_page_data[key] = value
                added_keys.append(key)
                
    # 5. Aggiorna il nodo del linguaggio
    texts_data[page_id][lang] = new_page_data
    
    # 6. Salva il file texts.json aggiornato
    try:
        with open(TEXTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(texts_data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ texts.json aggiornato con successo. Aggiunte/Modificate chiavi: {', '.join(added_keys)}")
    except Exception as e:
        print(f"ERRORE durante il salvataggio di '{TEXTS_FILE}': {e}")


# --- LOGICA DI ESECUZIONE ---
def main():
    """
    Funzione principale per l'esecuzione dello script. 
    Aggiorna texts.json per tutte le configurazioni generate in config_files.
    """
    print("Avvio sincronizzazione chiavi con texts.json (versione 3, Immagine Testata Unica)...")
    
    if not os.path.exists(CONFIG_DIR):
        print(f"ERRORE: La directory '{CONFIG_DIR}' non esiste.")
        return

    # Cerca file nel formato page_config_[lang]_[pageId].json
    config_files = [f for f in os.listdir(CONFIG_DIR) if FILENAME_PATTERN.match(f)]
    
    if not config_files:
        print(f"Nessun file di configurazione JSON trovato in '{CONFIG_DIR}' con il formato atteso (page_config_LL_PP.json).")
        return

    for filename in config_files:
        filepath = os.path.join(CONFIG_DIR, filename)
        config_data = load_json(filepath)

        if config_data is None:
             print(f"AVVISO: File '{filename}' saltato a causa di errore di caricamento.")
             continue

        # Estrae lang e page_id dal nome del file usando il nuovo pattern regex
        match = FILENAME_PATTERN.match(filename)
        if match:
            lang, page_id = match.groups()
            
            # Nota: lang è il Gruppo 1, page_id è il Gruppo 2
            update_texts_json(page_id, lang, config_data)
        else:
            # Non dovrebbe mai succedere se la lista config_files è filtrata correttamente, 
            # ma lo teniamo per sicurezza.
            print(f"AVVISO: File di configurazione ignorato per formato non corrispondente al pattern inaspettato: {filename}")

if __name__ == "__main__":
    main()