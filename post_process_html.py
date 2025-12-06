import re
import json
import sys
import os
from typing import Dict, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Nome del file HTML grezzo generato dalla conversione DOCX (DA LEGGERE)
# Assicurati che il tuo script di conversione salvi l'output con questo nome.
TEMP_HTML_FILENAME = "raw_output.html" 
# Cartella dove verranno salvati i frammenti HTML e il file JSON di configurazione
OUTPUT_DIR = "OUTPUT_HTML" 

# --- REGEX PER PULIZIA E SPLIT ---

# 1. Regex per rimuovere tutti i tag <img> (Punto 3.a: eliminazione delle immagini)
# Rimuove qualsiasi tag immagine lasciato dal convertitore, ovunque si trovi.
IMG_TAG_REGEX = re.compile(r'<img[^>]*?>', re.IGNORECASE | re.DOTALL)

# 2. Regex per trovare E pulire il blocco di split e i suoi elementi HTML circostanti.
# Questo pattern cattura e rimuove l'intero blocco di split, inclusi <p> e spazi bianchi, 
# per garantire la massima pulizia del punto di giunzione.
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    r'(<p[^>]*>)?\s*\[SPLIT_BLOCK:(.*?)\]\s*(</p>)?', 
    re.IGNORECASE | re.DOTALL
)

def clean_html_content(html_content: str) -> str:
    """Rimuove i tag <img> e ripulisce le nuove linee/spazi superflui."""
    # Rimuove tutti i tag immagine
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    # Rimuove righe vuote e spazi multipli
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML grezzo: pulisce il markup dell'immagine, suddivide il contenuto (Punto 3.b) 
    e genera la struttura JSON per il mapping.
    """
    print(f"Inizio Elaborazione e Split: Pagina '{page_id.upper()}', Lingua '{lang}'")
    
    # --- STEP 1: RIMOZIONE E TOKENIZZAZIONE ---
    
    # Trova i nomi dei file immagine (il contenuto tra le parentesi quadre)
    split_matches = SPLIT_BLOCK_CLEANING_REGEX.findall(html_input)
    # Estrae solo il nome del file immagine (gruppo 2 nella regex)
    image_filenames = [match[1].strip() for match in split_matches] 
    
    # Sostituisce l'intero blocco sporco (tag <p> + placeholder) con un token di split pulito
    split_token = "---SPLIT-HERE---"
    content_with_tokens = SPLIT_BLOCK_CLEANING_REGEX.sub(split_token, html_input)

    # Suddivide il contenuto
    raw_fragments = content_with_tokens.split(split_token)

    # --- STEP 2: GENERAZIONE DATI E FILE ---
    
    fragments_html = {} # Contenuto dei file .html da scrivere
    json_data = {}      # Configurazione JSON da salvare
    fragment_index = 1
    
    for i, raw_html in enumerate(raw_fragments):
        
        cleaned_html = clean_html_content(raw_html)
        
        # Ignora i frammenti vuoti che possono essere generati dallo split
        if not cleaned_html:
            continue
            
        # Nomi delle chiavi e dei file (Convenzione: it_[pageID]_maintextX.html)
        main_text_key = f"mainText{fragment_index}"
        html_filepath = f"{lang}_{page_id}_{main_text_key}.html"
        
        # Salva il frammento HTML pulito 
        fragments_html[html_filepath] = cleaned_html
        
        # Aggiunge la chiave "mainTextX": "it_home_maintextX.html" al JSON
        json_data[main_text_key] = html_filepath

        # Associa l'immagine al frammento, se ne è stata trovata una nel blocco di split successivo
        if i < len(image_filenames):
            image_filename = image_filenames[i]
            image_source_key = f"imageSource{fragment_index}"
            
            # Genera il percorso come richiesto: [paginaID]/[nome_immagine.jpg]
            image_path_value = f"{page_id}/{image_filename}"
            # Aggiunge la chiave "imageSourceX": "home/nome_immagine.jpg" al JSON
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
    json_filename = f"page_config_{page_id}.json"
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)
    try:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            # ensure_ascii=False permette di salvare caratteri non ASCII (come gli accenti italiani) correttamente
            json.dump(data_json, f, indent=4, ensure_ascii=False)
        print(f"\nCreato file JSON di configurazione: {json_filepath}")
        print("Il file JSON mappa le chiavi mainTextX e imageSourceX.")
        print("\nPROCESSO COMPLETATO CON SUCCESSO.")
    except Exception as e:
        print(f"ERRORE nella scrittura del file JSON {json_filepath}: {e}")


if __name__ == "__main__":
    # Verifica gli argomenti della riga di comando: python script.py [page_id] [lang]
    if len(sys.argv) != 3:
        print(f"ERRORE: Argomenti mancanti.")
        print(f"Utilizzo: python {sys.argv[0]} [page_id] [lang]")
        print("Esempio: python {sys.argv[0]} home it")
        sys.exit(1)
        
    PAGE_ID = sys.argv[1]
    LANG = sys.argv[2]
    
    # --- CARICAMENTO DEL CONTENUTO HTML GREZZO ---
    
    raw_html_content = ""
    try:
        with open(TEMP_HTML_FILENAME, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        print(f"File grezzo '{TEMP_HTML_FILENAME}' letto con successo.")
    except FileNotFoundError:
        print(f"ERRORE FATALE: File HTML grezzo '{TEMP_HTML_FILENAME}' non trovato.")
        print("Assicurati che lo script di conversione (soffice) lo abbia creato correttamente.")
        sys.exit(1)
    except Exception as e:
        print(f"ERRORE durante la lettura del file HTML grezzo: {e}")
        sys.exit(1)
        
    # --- ESECUZIONE ---
    fragments, config_data = process_document(raw_html_content, LANG, PAGE_ID)
    save_results(fragments, config_data, PAGE_ID)