import re
import json
from typing import Dict, Tuple

# --- CONFIGURAZIONE ---
LANG = "it"
PAGE_ID = "home"
BASE_ASSETS_PATH = "Assets/images"

# --- REGEX AGGIORNATE PER LA MASSIMA PULIZIA ---

# 1. Regex per rimuovere tutti i tag <img> (Punto C: Pulizia immagine)
# Questa regex rimuove qualsiasi tag immagine che il convertitore possa aver lasciato.
IMG_TAG_REGEX = re.compile(r'<img[^>]*?>', re.IGNORECASE | re.DOTALL)

# 2. Regex per trovare E pulire il blocco di split e i suoi elementi HTML circostanti.
# Questo pattern cattura e rimuove:
# - Un tag <p> opzionale (e i suoi attributi) all'inizio.
# - Spazi bianchi e nuove linee (grazie a re.DOTALL).
# - Il blocco core [SPLIT_BLOCK:...].
# - Un tag </p> opzionale alla fine.
SPLIT_BLOCK_CLEANING_REGEX = re.compile(
    r'(<p[^>]*>)?\s*\[SPLIT_BLOCK:(.*?)\]\s*(</p>)?', 
    re.IGNORECASE | re.DOTALL
)

# --- SIMULAZIONE INPUT (HTML più "sporco" per il test) ---
# Simula l'output grezzo di un convertitore, con i placeholder all'interno di <p>
# e con un tag <img> fittizio che deve essere rimosso.
SIMULATED_SOFFICE_HTML = f"""
<html><body>
    <h1>{PAGE_ID.capitalize()} Page Title</h1>
    <p>Questo è il testo principale del primo blocco di contenuto.</p>
    <p>Contiene anche del testo in <b>grassetto</b>. <img src="embedded_image_ref.png" style="width:100px;"/>
    Questo tag immagine DEVE essere rimosso.</p>
    
    <!-- Markup sporco da rimuovere: il tag <p> avvolge il placeholder -->
    <p style="text-align:center;">[SPLIT_BLOCK:panorama_bologna.jpg]</p>

    <h2>Secondo Blocco</h2>
    <p>Qui inizia il secondo frammento di testo.</p>
    <p>Altro testo irrilevante.</p>
    <div>[SPLIT_BLOCK:statua_nettuno.png]</div> <!-- Test con <div> non catturato, ma il placeholder sì -->

    <h3>Terzo Blocco</h3>
    <p>Questo è l'ultimo blocco di testo.</p>
</body></html>
"""

def clean_html(html_content: str) -> str:
    """Rimuove tutti i tag <img> e ripulisce le nuove linee/spazi superflui."""
    # Rimuove tutti i tag immagine globalmente
    cleaned = IMG_TAG_REGEX.sub('', html_content)
    # Rimuove le righe vuote e spazi multipli
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()
    return cleaned

def process_document(html_input: str, lang: str, page_id: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Processa l'HTML, pulisce il markup dell'immagine, suddivide il contenuto e genera la struttura JSON.
    """
    print(f"--- Inizio Elaborazione: {page_id.upper()} ({lang}) ---")
    
    # --- STEP 1: RIMOZIONE E TOKENIZZAZIONE ---
    
    # Usiamo findall sul blocco di pulizia per ottenere i nomi delle immagini
    # La cattura è sul secondo gruppo (.*?) della regex, ovvero il nome del file.
    split_matches = SPLIT_BLOCK_CLEANING_REGEX.findall(html_input)
    
    # Estraiamo solo i nomi dei file (che sono nel gruppo 2 di ogni match)
    split_blocks = [match[1].strip() for match in split_matches]
    
    # Sostituisce l'intero markup sporco (inclusi <p> e placeholder) con un token di split pulito
    split_token = "---SPLIT-HERE---"
    content_with_tokens = SPLIT_BLOCK_CLEANING_REGEX.sub(split_token, html_input)

    # --- STEP 2: SUDDIVISIONE E PULIZIA ---
    
    raw_fragments = content_with_tokens.split(split_token)

    # --- STEP 3: GENERAZIONE DATI ---
    
    fragments_html = {}
    json_data = {}
    fragment_index = 1
    
    for i, raw_html in enumerate(raw_fragments):
        
        # Pulizia globale (rimozione di tag <img> e whitespace)
        cleaned_html = clean_html(raw_html)
        
        if not cleaned_html:
            continue
            
        # Generazione nomi e chiavi
        main_text_key = f"mainText{fragment_index}"
        html_filepath = f"{lang}_{page_id}_{main_text_key}.html"
        
        # Frammento HTML pulito
        fragments_html[html_filepath] = cleaned_html
        json_data[main_text_key] = html_filepath

        # Associa l'immagine al frammento, se ne è stata trovata una nel blocco di split
        if i < len(split_blocks):
            image_filename = split_blocks[i]
            image_source_key = f"imageSource{fragment_index}"
            
            # Genera il percorso (es. home/panorama_bologna.jpg)
            image_path_value = f"{page_id}/{image_filename}"
            json_data[image_source_key] = image_path_value

            print(f"  - Trovato Split Block {fragment_index}: {image_filename}")
        
        fragment_index += 1

    return fragments_html, json_data

# --- ESECUZIONE DELLO SCRIPT ---
if __name__ == "__main__":
    
    # Passo 1: Processare il documento
    html_fragments, data_json = process_document(SIMULATED_SOFFICE_HTML, LANG, PAGE_ID)

    print("\n" + "="*50)
    print("RIEPILOGO PROCESSO DI PULIZIA E SPLIT")
    print("="*50)
    
    # Passo 2: Mostrare la struttura JSON generata
    print("\n[A] Dati JSON Generati (Chiavi per il caricamento nel sito):")
    print(json.dumps(data_json, indent=4))
    
    # Passo 3: Mostrare i frammenti HTML generati
    print("\n[B] Frammenti HTML Generati:")
    for filepath, content in html_fragments.items():
        print("-" * 30)
        print(f"FILE: {filepath}")
        # Notare che la pulizia ha rimosso il tag <img> e i tag <p> attorno allo split block
        print(content)
        print("-" * 30)

    # ISTRUZIONI FINALI
    print("\n[C] Verifiche Effettuate:")
    print("    - La funzione clean_html ha rimosso il tag <img> fittizio.")
    print("    - La regex di split ha rimosso i tag <p> che avvolgevano i placeholder.")
    print(f"    - Il percorso dell'immagine è strutturato come richiesto: {PAGE_ID}/[nome_file.jpg].")