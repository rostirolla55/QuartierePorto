import re
import json
import sys
import os
from typing import Dict, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Nome del file HTML grezzo generato dalla conversione DOCX (DA LEGGERE)
TEMP_HTML_FILENAME = "raw_output.html" 
# Cartella dove verranno salvati i frammenti HTML e il file JSON di configurazione
OUTPUT_DIR = "text_files" 

# --- REGEX PER PULIZIA E SPLIT ---

# Rimuove tutti i tag <img>
IMG_TAG_REGEX = re.compile(r'<img[^>]*?>', re.IGNORECASE | re.DOTALL)

# Rimuove il blocco di split, inclusi i tag <p> e spazi bianchi circostanti.
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    r'(<p[^>]*>)?\s*\[SPLIT_BLOCK:(.*?)\]\s*(</p>)?', 
    re.IGNORECASE | re.DOTALL
)

def clean_html_content(html_content: str) -> str:
    """Rimuove i tag <img> e ripulisce le nuove linee/spazi superflui."""
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML grezzo: pulisce il markup dell'immagine, suddivide il contenuto
    e genera la struttura JSON per il mapping.
    """
    # Usiamo page_id.upper() solo per il log, non per i nomi dei file.
    print(f"Inizio Elaborazione e Split: Pagina '{page_id.upper()}', Lingua '{lang}'")
    
    # --- STEP 1: RIMOZIONE E TOKENIZZAZIONE ---
    
    # Trova i nomi dei file immagine (il contenuto tra le parentesi quadre)
    split_matches = SPLIT_BLOCK_CLEANING_REGEX.findall(html_input)
    image_filenames = [match[1].strip() for match in split_matches] 
    
    # Sostituisce l'intero blocco sporco con un token di split pulito
    split_token = "---SPLIT-HERE---"
    content_with_tokens = SPLIT_BLOCK_CLEANING_REGEX.sub(split_token, html_input)

    # Suddivide il contenuto
    raw_fragments = content_with_tokens.split(split_token)

    # --- STEP 2: GENERAZIONE DATI E FILE ---
    
    fragments_html = {} 
    json_data = {}      
    fragment_index = 1
    
    for i, raw_html in enumerate(raw_fragments):
        
        cleaned_html = clean_html_content(raw_html)
        
        if not cleaned_html:
            continue
            
        # CHIAVE JSON (CamelCase - per l'applicazione)
        main_text_key = f"mainText{fragment_index}"
        
        # NOME DEL FILE (Minuscolo - per la massima compatibilità sul server)
        file_base_name = main_text_key.lower()
        # Costruzione del nome del file interamente in minuscolo
        html_filepath = f"{lang}_{page_id}_{file_base_name}.html" 
        
        # Salva il frammento HTML pulito 
        fragments_html[html_filepath] = cleaned_html
        
        # Aggiunge la chiave JSON: "mainText1": "it_home_maintext1.html"
        json_data[main_text_key] = html_filepath

        # Gestione dei riferimenti immagine
        if i < len(image_filenames):
            image_filename = image_filenames[i]
            
            # CHIAVE JSON per l'immagine (CamelCase)
            image_source_key = f"imageSource{fragment_index}" 
            
            # VALORE per l'immagine (percorso, manteniamo la coerenza con page_id in minuscolo)
            image_path_value = f"{page_id.lower()}/{image_filename.lower()}" # Aggiunto lower() anche per il nome file immagine
            json_data[image_source_key] = image_path_value

            print(f"  - Associato Frammento {fragment_index} al riferimento immagine: {image_path_value}")
        
        fragment_index += 1

    return fragments_html, json_data

def save_results(fragments: Dict[str, str], data_json: Dict[str, str], page_id: str):
    """Salva i frammenti HTML e il file JSON di configurazione nella cartella di output."""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Salva i file frammento HTML
    for filename, content in fragments.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Creato file frammento: {filepath}")
        except Exception as e:
            print(f"ERRORE nella scrittura del file {filepath}: {e}")

    # Salva il file JSON di configurazione della pagina
    json_filename = f"page_config_{page_id.lower()}.json"
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)
    try:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_json, f, indent=4, ensure_ascii=False)
        print(f"\nCreato file JSON di configurazione: {json_filepath}")
        print("Il file JSON mappa le chiavi mainTextX e imageSourceX.")
        print("\nPROCESSO COMPLETATO CON SUCCESSO.")
    except Exception as e:
        print(f"ERRORE nella scrittura del file JSON {json_filepath}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"ERRORE: Argomenti mancanti.")
        print(f"Utilizzo: python {sys.argv[0]} [page_id] [lang]")
        print("Esempio: python {sys.argv[0]} home it")
        sys.exit(1)
        
    # Convertiamo immediatamente page_id e lang in minuscolo per tutti gli usi nel file naming
    # Nota: Anche se l'utente dovesse inserire "Home", qui viene convertito in "home"
    PAGE_ID = sys.argv[1].lower()
    LANG = sys.argv[2].lower()
    
    # --- CARICAMENTO DEL CONTENUTO HTML GREZZO ---
    
    raw_html_content = ""
    try:
        with open(TEMP_HTML_FILENAME, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        print(f"File grezzo '{TEMP_HTML_FILENAME}' letto con successo.")
    except FileNotFoundError:
        print(f"ERRORE FATALE: File HTML grezzo '{TEMP_HTML_FILENAME}' non trovato.")
        sys.exit(1)
    except Exception as e:
        print(f"ERRORE durante la lettura del file HTML grezzo: {e}")
        sys.exit(1)
        
    # --- ESECUZIONE ---
    fragments, config_data = process_document(raw_html_content, LANG, PAGE_ID)
    save_results(fragments, config_data, PAGE_ID)