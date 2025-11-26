import sys
import os
import json

# --- CONFIGURAZIONE ---
# Questa costante punta alla cartella dove si trovano i file HTML/TXT da caricare
TEXT_FILES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'text_files') 
JSON_BASE_PATH = "data/translations"
LANGUAGES = ['it', 'en', 'es', 'fr']

def read_file_content(filename):
    """Legge il contenuto di un file e lo restituisce come stringa."""
    full_path = os.path.join(TEXT_FILES_PATH, filename)
    
    # Tentativo di leggere il file con codifica UTF-8
    try:
        # Aggiungo print per debug in caso di errore FileNotFoundError
        print(f"-> Tentativo di leggere il contenuto da: {full_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Sostituiamo gli a capo con '\n' per preservare la formattazione nel JSON
        # Assumiamo che il contenuto sia già stato sanificato (es. da sanitize_text.py)
        return content.strip().replace('\n', '\\n').replace('"', '\\"')
    except FileNotFoundError:
        print(f"ERRORE: File di testo sorgente non trovato: {full_path}")
        return None
    except Exception as e:
        print(f"ERRORE di lettura del file {filename}: {e}")
        return None

def update_json_key(lang_code, full_key, value_or_filename):
    """
    Aggiorna il valore di una chiave annidata. Se il valore fornito è un nome di file,
    legge il contenuto di quel file e lo inserisce nel JSON.
    """
    if lang_code not in LANGUAGES:
        print(f"ERRORE: Codice lingua '{lang_code}' non valido. Deve essere tra {LANGUAGES}.")
        return False
        
    try:
        page_id, key_name = full_key.split('.', 1)
    except ValueError:
        print(f"ERRORE: Chiave non valida. Formato atteso: 'page_id.key'. Ricevuto: '{full_key}'")
        return False

    json_path = os.path.join(JSON_BASE_PATH, lang_code, "texts.json")
    
    if not os.path.exists(json_path):
        print(f"ERRORE: File JSON non trovato per la lingua '{lang_code}' in: {json_path}")
        return False
        
    print(f"-> Aggiornamento di {lang_code}/texts.json per la chiave {full_key}...")
    
    # --- LOGICA DI CARICAMENTO DEL CONTENUTO ---
    final_value = value_or_filename
    
    # Se il valore in input e' un file (.html o .txt), leggiamo il suo contenuto
    if value_or_filename.lower().endswith(('.html', '.txt')):
        # Il file da caricare si trova in text_files
        print(f"-> Trovato nome file '{value_or_filename}'. Tentativo di caricamento contenuto...")
        
        # Tentativo di leggere il contenuto del file
        content = read_file_content(value_or_filename)
        
        if content is None:
            # La lettura è fallita (es. File non trovato). Esci con errore.
            print("❌ Operazione interrotta per errore di lettura file.")
            return False
            
        final_value = content
        print("-> Contenuto letto con successo. Passaggio alla scrittura nel JSON.")

    # --- SCRITTURA NEL JSON ---
    try:
        # Legge il file JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if page_id not in data:
            print(f"ERRORE: ID pagina '{page_id}' non trovato nel file JSON.")
            return False
            
        # Aggiorna la chiave specifica all'interno del blocco della pagina
        data[page_id][key_name] = final_value
        
        # Scrive il file JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False per preservare i caratteri UTF-8 come gli emoji
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        print(f"✅ Aggiornato con successo: '{full_key}'. Valore finale (truncate): '{final_value[:50]}...'")
        return True

    except Exception as e:
        print(f"ERRORE durante l'operazione su texts.json: {e}")
        return False

# --- Entry Point ---
if __name__ == "__main__":
    # La parte di setup del PATH per 'text_files' è cruciale. 
    # Per semplicità, in ambiente Windows, è spesso meglio che questo script
    # venga eseguito dalla cartella root del progetto, o che il Batch 
    # stabilisca il path assoluto per i file sorgente.
    # Assumendo che il Batch (update_json.bat) sia eseguito correttamente,
    # qui ci preoccupiamo solo dell'aggiornamento.
    
    if len(sys.argv) != 4:
        print("USO: python update_json_key.py <codice_lingua> <id_pagina.chiave> <valore_o_nomefile>")
        sys.exit(1)
        
    lang_code = sys.argv[1].lower()
    full_key = sys.argv[2]
    # Usiamo quotes nel Batch per includere spazi, ma il nome del file deve essere ripulito
    value_or_filename = sys.argv[3].strip('"') 
    
    if not update_json_key(lang_code, full_key, value_or_filename):
        sys.exit(1)
        
    sys.exit(0)