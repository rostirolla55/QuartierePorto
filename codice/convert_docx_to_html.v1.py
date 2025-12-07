import re
import json
import sys
import os
from typing import Dict, Tuple

# --- CONFIGURAZIONE GLOBALE ---

# Assumiamo che il file HTML grezzo sia salvato in una cartella temporanea
TEMP_HTML_FILENAME = "raw_output.html" 
OUTPUT_DIR = "processed_fragments" # Cartella dove salvare i file .html e .json

# --- REGEX PER PULIZIA E SPLIT ---

# 1. Regex per rimuovere tutti i tag <img>
IMG_TAG_REGEX = re.compile(r'<img[^>]*?>', re.IGNORECASE | re.DOTALL)

# 2. Regex per trovare E pulire il blocco di split e i suoi elementi HTML circostanti.
# Questo pattern cattura e rimuove:
# - Un tag <p> opzionale (e i suoi attributi) all'inizio.
# - Spazi bianchi e nuove linee.
# - Il blocco core [SPLIT_BLOCK:...].
# - Un tag </p> opzionale alla fine.
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    r'(<p[^>]*>)?\s*\[SPLIT_BLOCK:(.*?)\]\s*(</p>)?', 
    re.IGNORECASE | re.DOTALL
)

def clean_html_content(html_content: str) -> str:
    """Rimuove i tag <img> e ripulisce le nuove linee/spazi superflui."""
    # Rimuove tutti i tag immagine (Punto c: pulizia immagine)
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    # Rimuove righe vuote e spazi multipli
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML, pulisce il markup dell'immagine, suddivide il contenuto e genera la struttura JSON.
    """
    print(f"Inizio Elaborazione: {page_id.upper()} ({lang})")
    
    # --- STEP 1: RIMOZIONE E TOKENIZZAZIONE ---
    
    # Trova i nomi dei file immagine contenuti nel blocco di split
    split_matches = SPLIT_BLOCK_CLEANING_REGEX.findall(html_input)
    split_blocks = [match[1].strip() for match in split_matches] # Estrae solo il nome del file immagine
    
    # Sostituisce l'intero markup sporco (<p> + placeholder) con un token di split pulito (Punto d)
    split_token = "---SPLIT-HERE---"
    content_with_tokens = SPLIT_BLOCK_CLEANING_REGEX.sub(split_token, html_input)

    # Suddivide il contenuto
    raw_fragments = content_with_tokens.split(split_token)

    # --- STEP 2: GENERAZIONE DATI E FILE ---
    
    fragments_html = {} # Per salvare i contenuti dei file .html
    json_data = {}      # Per salvare la configurazione JSON
    fragment_index = 1
    
    for i, raw_html in enumerate(raw_fragments):
        
        cleaned_html = clean_html_content(raw_html)
        
        if not cleaned_html:
            continue
            
        # Nomi delle chiavi e dei file (Punto e)
        main_text_key = f"mainText{fragment_index}"
        html_filepath = f"{lang}_{page_id}_{main_text_key}.html"
        
        # Salva il frammento HTML pulito (per la scrittura su disco)
        fragments_html[html_filepath] = cleaned_html
        
        # Aggiunge la chiave mainTextX alla struttura JSON
        json_data[main_text_key] = html_filepath

        # Se è stato trovato un blocco di split DOPO questo frammento
        if i < len(split_blocks):
            image_filename = split_blocks[i]
            image_source_key = f"imageSource{fragment_index}"
            
            # Genera il percorso come richiesto: [paginaID]/[nome_immagine.jpg]
            image_path_value = f"{page_id}/{image_filename}"
            json_data[image_source_key] = image_path_value

            print(f"  - Associato Frammento {fragment_index} all'immagine: {image_filename}")
        
        fragment_index += 1

    return fragments_html, json_data

def save_results(fragments: Dict[str, str], data_json: Dict[str, str], page_id: str):
    """Salva i frammenti HTML e il file JSON di configurazione nella cartella di output."""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Salva i file frammento HTML
    for filename, content in fragments.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Creato file frammento: {filepath}")

    # Salva il file JSON di configurazione della pagina
    json_filename = f"page_config_{page_id}.json"
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)
    print(f"\nCreato file JSON di configurazione: {json_filepath}")
    print("\nPROCESSO COMPLETATO CON SUCCESSO.")


if __name__ == "__main__":
    # Verifica gli argomenti della riga di comando: python script.py [page_id] [lang]
    if len(sys.argv) != 3:
        print(f"Utilizzo: python {sys.argv[0]} [page_id] [lang]")
        print("Esempio: python {sys.argv[0]} home it")
        sys.exit(1)
        
    PAGE_ID = sys.argv[1]
    LANG = sys.argv[2]
    
    # --- SIMULAZIONE PER LA DEMO (In ambiente reale, leggere TEMP_HTML_FILENAME) ---
    
    # In un'implementazione reale, dovreste avere il contenuto HTML grezzo qui.
    # Ad esempio:
    # with open(TEMP_HTML_FILENAME, 'r', encoding='utf-8') as f:
    #     raw_html_content = f.read()

    # Per questa simulazione, usiamo un contenuto fittizio ma pulibile:
    SIMULATED_RAW_HTML = f"""
        <html><body>
            <!-- Immagine da rimuovere (Punto c) -->
            <img src="embedded_ref_01.png" style="width:100%"/>
            <h1>Titolo Pagina {PAGE_ID}</h1>
            <p>Testo del primo frammento.</p>
            <p>Questo contenuto include testo e tag base.</p>
            
            <p class="MsoNormal" style="text-align:center;">[SPLIT_BLOCK:panorama_bologna.jpg]</p>

            <h2>Sottotitolo Blocco 2</h2>
            <p>Inizio del secondo frammento.</p>
            
            <p>[SPLIT_BLOCK:statua_nettuno.png]</p>
            
            <h3>Blocco 3</h3>
            <p>Testo finale. Questo è l'ultimo frammento della pagina.</p>
        </body></html>
    """
    raw_html_content = SIMULATED_RAW_HTML
    
    # --- ESECUZIONE ---
    fragments, config_data = process_document(raw_html_content, LANG, PAGE_ID)
    save_results(fragments, config_data, PAGE_ID)