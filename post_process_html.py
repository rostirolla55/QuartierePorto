import re
import json
import sys
import os
from typing import Dict, Tuple

# NOTE: Rimozione dell'import di BeautifulSoup, in quanto l'analisi e la pulizia
# vengono ora gestite con le espressioni regolari (re).

# --- CONFIGURAZIONE GLOBALE ---

# Nome del file HTML grezzo generato dalla conversione DOCX (DA LEGGERE)
TEMP_HTML_FILENAME = "raw_output.html"
# Cartella dove verranno salvati i frammenti HTML e il file JSON di configurazione
OUTPUT_DIR = "text_files"

# --- REGEX PER PULIZIA E SPLIT ---

# Rimuove tutti i tag <img>
IMG_TAG_REGEX = re.compile(r'<img[^>]*?>', re.IGNORECASE | re.DOTALL)

# Cattura il contenuto tra le parentesi quadre, es: [SPLIT_BLOCK:nomefile.jpg]
# NOTA: Questo regex è usato solo per debug, non per lo split effettivo.
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    # Cattura TUTTI i caratteri (anche tag HTML e whitespace)
    r'.*?(\[SPLIT_BLOCK:(.*?)\]).*?',
    re.IGNORECASE | re.DOTALL
)

# =========================================================================
# FUNZIONE DI UTILITY PER DETERMINARE IL PREFISSO DEL NOME DEL FILE
# =========================================================================

def get_fragment_prefix(page_id: str) -> str:
    """
    Determina il prefisso da usare per i nomi dei file frammenti HTML.
    Se il PAGE_ID è 'home' (chiave JSON), il prefisso del file sarà 'index'.
    Altrimenti, usa il PAGE_ID stesso.
    """
    if page_id.lower() == 'home':
        # La pagina fisica è index-lang.html, quindi anche il frammento usa index come prefisso
        return 'index'
    return page_id


def clean_html_content(html_content: str) -> str:
    """Rimuove i tag <img> e ripulisce le nuove linee/spazi superflui."""
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    # Rimuove le doppie nuove righe/spazi e tag <p> e </p> vuoti dopo la rimozione immagini.
    cleaned = re.sub(r'(<p[^>]*>\s*</p>|\n\s*\n)', '\n', cleaned).strip()
    return cleaned

# =========================================================================
# FUNZIONE PER PULIZIA SPECIFICA DEI MARCATORI SPLIT
# =========================================================================

def sanitize_split_markers(html_content: str) -> str:
    """
    Applica una pre-pulizia all'HTML per rimuovere i tag HTML indesiderati 
    (come <u>, <strong>, <span>) che il convertitore DOCX introduce all'interno 
    del marker [SPLIT_BLOCK:...], che altrimenti impedirebbero il riconoscimento 
    della RegEx principale.
    
    Il pattern cerca il marcatore contaminato e rimuove tutti i tag <...> al suo interno.
    """
    print("DEBUG: Pre-pulizia dei marcatori SPLIT...")
    
    # Pattern per trovare l'intera area che va da '[' a ']' contenente SPLIT_BLOCK
    contamination_area_pattern = re.compile(r'\[[^\]]*?SPLIT_BLOCK[^\]]*?\]', re.IGNORECASE | re.DOTALL)
    
    def clean_match(match):
        # Prende il testo trovato (es. [<u>SPLIT</u>_BLOCK:AdorazionePastori.jpg])
        contaminated_text = match.group(0)
        
        # Rimuove tutti i tag HTML dall'interno (es. <u>, </u>)
        cleaned_text = re.sub(r'<\/?\w+[^>]*?>', '', contaminated_text)
        
        # Rimuove spazi extra e ritorna la stringa pulita (es. [SPLIT_BLOCK:AdorazionePastori.jpg])
        return cleaned_text.strip()

    # Sostituisce tutte le aree contaminate con la versione pulita
    sanitized_content = contamination_area_pattern.sub(clean_match, html_content)
    
    if sanitized_content != html_content:
        print("DEBUG: Trovati e puliti marcatori SPLIT contaminati da HTML.")
    
    return sanitized_content


def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML grezzo: pulisce il markup dell'immagine, suddivide il contenuto
    e genera la struttura JSON per il mapping.
    """
    page_id_lower = page_id.lower()
    print(f"Inizio Elaborazione e Split: Pagina '{page_id.upper()}', Lingua '{lang}'")

    # Determina il prefisso del file (sarà 'index' se page_id è 'home', altrimenti page_id)
    fragment_file_prefix = get_fragment_prefix(page_id_lower)
    print(f"DEBUG: Prefisso per i nomi dei file frammento: '{fragment_file_prefix}'")

    # --- STEP 0: PRE-PULIZIA DEL MARKER SPLIT ---
    # Risolve il problema del markup indesiderato (es. <u>) all'interno di [SPLIT_BLOCK:...]
    html_input = sanitize_split_markers(html_input)

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
        
        # *** UTILIZZO DEL PREFISSO CORRETTO ***
        # Assicura che il nome del file includa la lingua E il prefisso corretto (index o page_id)
        html_filepath = f"{lang}_{fragment_file_prefix}_{file_base_name}.html" 

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

# Questa funzione salva i frammenti HTML e il file JSON di configurazione
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

    # Salva il file JSON di configurazione della pagina (page_config_xx_pageID.json)
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


# Sezione principale per l'esecuzione dello script
if __name__ == "__main__":
    # --- Gestione Argomenti da Linea di Comando ---
    if len(sys.argv) != 4:
        print(f"ERRORE: Argomenti mancanti.")
        print(f"Utilizzo: python {sys.argv[0]} [page_id] [lang] [docx_dir]")
        print("Esempio: python {sys.argv[0]} pioggia3 it DOCS_DA_CONVERTIRE")
        sys.exit(1)

    # Definisce le variabili
    PAGE_ID = sys.argv[1].lower()
    LANG = sys.argv[2].lower() # Argumento lingua
    DOCX_DIR = sys.argv[3] # Directory contenente il file temporaneo
    
    print(f"Inizio elaborazione per ID Pagina: {PAGE_ID}, Lingua: {LANG}")
    
    # --- CARICAMENTO DEL CONTENUTO HTML GREZZO ---
    
    raw_html_content = ""
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
    
    # Chiamata alla funzione di salvataggio, passando la lingua
    save_results(fragments, config_data, PAGE_ID, LANG)
    
    # --- PULIZIA DEL FILE TEMPORANEO ---
    print(f"Pulizia del file temporaneo {TEMP_HTML_FILENAME} in {DOCX_DIR}...")
    try:
        os.remove(full_html_path)
        print("Pulizia completata.")
    except OSError as e:
        print(f"ATTENZIONE: Impossibile eliminare il file temporaneo {full_html_path}: {e}")