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

# Cattura il contenuto tra le parentesi quadre, es: [SPLIT_BLOCK:nomefile.jpg]
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    # Cattura TUTTI i caratteri (anche tag HTML e whitespace)
    r'.*?(\[SPLIT_BLOCK:(.*?)\]).*?',
    re.IGNORECASE | re.DOTALL
)


def clean_html_content(html_content: str) -> str:
    """Rimuove i tag <img> e ripulisce le nuove linee/spazi superflui."""
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    # Rimuove le doppie nuove righe/spazi e tag <p> e </p> vuoti dopo la rimozione immagini.
    cleaned = re.sub(r'(<p[^>]*>\s*</p>|\n\s*\n)', '\n', cleaned).strip()
    return cleaned

def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML grezzo: pulisce il markup dell'immagine, suddivide il contenuto
    e genera la struttura JSON per il mapping.
    """
    page_id_lower = page_id.lower()
    print(f"Inizio Elaborazione e Split: Pagina '{page_id.upper()}', Lingua '{lang}'")

    # --- STEP 1: RIMOZIONE E TOKENIZZAZIONE ---

    split_token = "---SPLIT-HERE---"
    image_filenames = []
    
    # Pattern per trovare l'intero blocco, inclusi eventuali tag P circostanti
    # Questo è più sicuro per l'estrazione: cattura il nome file nel gruppo 2
    # Esempio: <p>[SPLIT_BLOCK:nome.jpg]</p>
    extraction_regex = re.compile(
        r'(<p[^>]*>)?\s*\[SPLIT_BLOCK:(.*?)\]\s*(</p>)?',
        re.IGNORECASE | re.DOTALL
    )

    # 1. Trova TUTTE le occorrenze
    split_matches = extraction_regex.findall(html_input)

    # 2. Estrai solo i nomi dei file.
    image_filenames = [match[1].strip() for match in split_matches]

    # *** DEBUG CRITICO ***
    print(f"\n--- RISULTATO DEBUG REGEX ---")
    print(f"Trovati {len(image_filenames)} nomi file immagine. Lista: {image_filenames}")

    if not image_filenames and '[SPLIT_BLOCK:' in html_input:
        print("ATTENZIONE: Il marker [SPLIT_BLOCK] è presente, ma la REGEX non lo cattura [Controllare encoding/spazi non visibili].")
    print("-----------------------------\n")

    # 3. Sostituisce l'intero blocco sporco con un token di split pulito
    # Usiamo lo stesso regex di estrazione per la sostituzione (sub)
    content_with_tokens = extraction_regex.sub(split_token, html_input)

    # 4. Suddivide il contenuto. I raw_fragments sono i blocchi di testo tra i marker.
    raw_fragments = content_with_tokens.split(split_token)

    # *** DEBUG CRITICO 2 ***
    print(f"Trovati {len(raw_fragments)} frammenti di testo grezzi prima della pulizia.")
    # Stampa i primi 50 caratteri di ogni frammento
    for i, frag in enumerate(raw_fragments):
        print(f"  Frammento {i+1} (Inizio): {frag[:50].strip()}...")
    print("------------------------------------------------------\n")


    # --- STEP 2: GENERAZIONE DATI E FILE ---

    fragments_html = {}  # Contiene {nome_file_html: contenuto_html}
    json_data = {}       # Contiene {mainTextX: percorso_html, imageSourceX: percorso_immagine}
    fragment_index = 1

    # Processa ogni frammento di testo
    for i, raw_html in enumerate(raw_fragments):

        cleaned_html = clean_html_content(raw_html)

        # Ignora i frammenti vuoti (spesso l'ultimo frammento dopo un marker di split finale)
        # Il primo frammento (i=0) potrebbe essere vuoto se il marker è all'inizio.
        if not cleaned_html:
            continue

        # 1. GESTIONE TESTO (mainTextX)
        main_text_key = f"mainText{fragment_index}"
        file_base_name = main_text_key.lower()
        html_filepath = f"{lang}_{page_id_lower}_{file_base_name}.html"

        fragments_html[html_filepath] = cleaned_html
        json_data[main_text_key] = html_filepath

        print(f"  - Creato Frammento di Testo {fragment_index}: {html_filepath}")

        # 2. GESTIONE IMMAGINE (imageSourceX)
        # L'immagine N è associata al Frammento N.

        # Controlliamo che l'indice corrente del frammento (fragment_index - 1)
        # non superi il numero di immagini trovate.
        image_index = fragment_index - 1

        if image_index < len(image_filenames):
            image_filename = image_filenames[image_index]

            image_source_key = f"imageSource{fragment_index}"

            # Percorso web: pioggia3/AdorazionePastori.jpg.
            image_path_value = f"{page_id_lower}/{image_filename}"

            json_data[image_source_key] = image_path_value
            print(f"  - Associato Immagine {fragment_index} al riferimento: {image_path_value}")

        fragment_index += 1

    return fragments_html, json_data

# CORREZIONE 1: Aggiunta di 'lang' alla firma della funzione save_results
def save_results(fragments: Dict[str, str], data_json: Dict[str, str], page_id: str, lang: str):
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
    # CORREZIONE 2: Uso della variabile 'lang' definita localmente
    json_filename = f"page_config_{lang}_{page_id}.json"
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
    # CORREZIONE 1: Ora ci si aspetta 4 argomenti: [script] [page_id] [lang] [docx_dir]
    if len(sys.argv) != 4:
        print(f"ERRORE: Argomenti mancanti.")
        print(f"Utilizzo: python {sys.argv[0]} [page_id] [lang] [docx_dir]")
        print("Esempio: python {sys.argv[0]} pioggia3 it DOCS_DA_CONVERTIRE")
        sys.exit(1)

    PAGE_ID = sys.argv[1].lower()
    LANG = sys.argv[2].lower()
    DOCX_DIR = sys.argv[3] # L'argomento 3 è la directory
    
    # --- CARICAMENTO DEL CONTENUTO HTML GREZZO ---
    
    raw_html_content = ""
    # CORREZIONE 2: Costruisci il percorso completo usando la directory passata come argomento
    full_html_path = os.path.join(DOCX_DIR, TEMP_HTML_FILENAME)
    
    try:
        with open(full_html_path, 'r', encoding='utf-8') as f:
            raw_html_content = f.read()
        print(f"File grezzo '{full_html_path}' letto con successo.")
    except FileNotFoundError:
        print(f"ERRORE FATALE: File HTML grezzo '{full_html_path}' non trovato. Controllare percorso/rinomina.")
        sys.exit(1)
    except Exception as e:
        print(f"ERRORE durante la lettura del file HTML grezzo: {e}")
        sys.exit(1)
        
    # --- ESECUZIONE ---
    fragments, config_data = process_document(raw_html_content, LANG, PAGE_ID)
    # CORREZIONE 3: Passaggio dell'argomento LANG
    save_results(fragments, config_data, PAGE_ID, LANG)
    
    # --- PULIZIA DEL FILE TEMPORANEO ---
    # Questa parte era mancante, ma è buona pratica rimuovere il file temporaneo
    print(f"Pulizia del file temporaneo {TEMP_HTML_FILENAME} in {DOCX_DIR}...")
    try:
        os.remove(full_html_path)
        print("Pulizia completata.")
    except OSError as e:
        print(f"ATTENZIONE: Impossibile eliminare il file temporaneo {full_html_path}: {e}")