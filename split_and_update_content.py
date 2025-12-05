import os
import re
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, List

# =================================================================
# COSTANTI DI CONFIGURAZIONE
# =================================================================

# Questa è la cartella dove si trovano i file DOCX di input e dove
# verranno salvati tutti i file di output (HTML, JSON).
OUTPUT_DIR = "text_files"

# Nome del file JSON di configurazione principale da aggiornare
CONFIG_JSON_FILE = os.path.join(OUTPUT_DIR, "config.json")

# =================================================================
# FUNZIONI DI SUPPORTO
# =================================================================

def clean_html_content(html_content: str) -> str:
    """
    Rimuove i tag indesiderati e le classi di formattazione non necessarie
    dal contenuto HTML grezzo generato da LibreOffice.
    """
    # 1. Rimuovi i tag superflui generati da LibreOffice/Word
    html_content = re.sub(r'<(div|span)\s+[^>]*>', '', html_content)
    html_content = re.sub(r'</(div|span)>', '', html_content)

    # 2. Rimuovi gli attributi di stile e classe
    html_content = re.sub(r' style="[^"]*"', '', html_content)
    html_content = re.sub(r' class="[^"]*"', '', html_content)

    # 3. Pulisci gli spazi bianchi multipli
    html_content = re.sub(r'\s+', ' ', html_content).strip()

    return html_content

def load_config_data(config_path: str) -> Dict[str, Any]:
    """Carica i dati JSON dal file di configurazione o inizializza se non esiste."""
    if not os.path.exists(config_path):
        print(f"AVVISO: File di configurazione non trovato in '{config_path}'. Creazione di una nuova struttura JSON.")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERRORE: Impossibile decodificare il file JSON '{config_path}'. Il file è corrotto o vuoto.")
        # Restituisce una struttura vuota per prevenire il blocco
        return {}
    except Exception as e:
        print(f"ERRORE di caricamento JSON: {e}")
        return {}


def save_config_data(config_path: str, data: Dict[str, Any]):
    """Salva la struttura dati JSON nel file di configurazione."""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"File di configurazione aggiornato con successo: {config_path}")
    except Exception as e:
        print(f"ERRORE di salvataggio JSON: {e}")

# =================================================================
# LOGICA PRINCIPALE
# =================================================================

def split_and_update_content(html_filepath: str, page_id: str, lang: str, config_path: str):
    """
    Legge il contenuto HTML, lo suddivide in testo principale e testo modale,
    e aggiorna il file JSON di configurazione.
    """
    
    # 1. Leggi il contenuto HTML
    try:
        with open(html_filepath, 'r', encoding='utf-8') as f:
            full_html = f.read()
    except FileNotFoundError:
        print(f"ERRORE: File HTML di input non trovato: {html_filepath}")
        return
    
    # 2. Analizza l'HTML
    # Utilizziamo BeautifulSoup per analizzare e navigare nell'albero DOM
    soup = BeautifulSoup(full_html, 'html.parser')

    # A. Estrai il TITOLO (usando il primo h1 trovato)
    title_element = soup.find('h1')
    page_title = title_element.get_text().strip() if title_element else "Titolo mancante"
    
    # Rimuovi il titolo dall'analisi successiva per non includerlo nel testo
    if title_element:
        title_element.decompose()
        
    # B. Estrai il testo principale e il testo del modale
    
    # Ipotizziamo che il testo modale sia contenuto tra i tag <hr>
    modal_content_raw = ""
    main_content_raw = ""
    
    # Trova il contenuto del BODY (o un contenitore più specifico se necessario)
    body_content = soup.find('body')
    if not body_content:
        print("AVVISO: Contenuto <body> non trovato nell'HTML.")
        return

    # Dividi il contenuto in base a un separatore (es. <hr> o un tag specifico)
    # Per semplicità, consideriamo il testo dopo l'ultimo <hr> come testo modale.
    
    content_parts = str(body_content).split('<hr/>') # LibreOffice spesso usa <hr/>
    
    if len(content_parts) > 1:
        # Se c'è un separatore <hr>, l'ultimo pezzo è il contenuto modale.
        # Rimuovi il tag body che è rimasto nel primo pezzo dello split
        main_content_soup = BeautifulSoup(content_parts[0].replace('<body>', ''), 'html.parser')
        
        # Estraiamo tutto il contenuto testuale e strutturale del main content
        main_content_raw = ''.join([str(tag) for tag in main_content_soup.body.contents])
        
        # Il contenuto modale è l'ultimo pezzo
        modal_content_raw = content_parts[-1].replace('</body>', '')
    else:
        # Se non c'è separatore, tutto il contenuto è testo principale.
        main_content_raw = ''.join([str(tag) for tag in body_content.contents])


    # 3. Pulizia e serializzazione
    
    # Pulisci il testo principale (rimuovi classi e tag superflui)
    main_content_cleaned = clean_html_content(main_content_raw)
    
    # Il contenuto del modale lo manteniamo il più possibile fedele, 
    # ma togliamo i tag superflui.
    modal_content_cleaned = clean_html_content(modal_content_raw)
    
    # 4. Aggiorna la struttura JSON
    config_data = load_config_data(config_path)

    # Crea la chiave unica per lingua e ID della pagina (es. "it_cavaticcio")
    page_key = f"{lang}_{page_id}"
    
    # Struttura di default
    if 'pages' not in config_data:
        config_data['pages'] = {}

    # Aggiorna i dati della pagina
    config_data['pages'][page_key] = {
        "title": page_title,
        "lang": lang,
        "main_text": main_content_cleaned,
        "modal_text": modal_content_cleaned,
        "last_updated_file": os.path.basename(html_filepath)
    }

    # 5. Salva i dati aggiornati
    save_config_data(config_path, config_data)
    
    # 6. Salvataggio del testo grezzo (opzionale, per debug)
    # Salva il contenuto pulito e formattato in un file di output HTML
    output_html_filename = os.path.join(OUTPUT_DIR, f"{lang}_{page_id}_processed_OUTPUT.html")
    try:
        with open(output_html_filename, 'w', encoding='utf-8') as f:
            f.write(f"<h1>{page_title}</h1>\n")
            f.write("<!-- Contenuto Principale -->\n")
            f.write(main_content_cleaned)
            f.write("\n\n<!-- Contenuto Modale (Separato da <hr/> nel DOCX) -->\n")
            f.write(modal_content_cleaned)
        print(f"Debug/Output HTML salvato in: {output_html_filename}")
    except Exception as e:
        print(f"ERRORE nel salvataggio del file di output HTML: {e}")


if __name__ == "__main__":
    # Esempio di utilizzo (per testare solo questo file)
    # Nota: Assicurati che esista un file HTML di input con il nome corretto
    # Esempio: "text_files/it_testpage_maintext_INPUT.html"
    
    # Creazione della directory se non esiste
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("--------------------------------------------------")
    print(f"ESECUZIONE DI TEST DELLO SCRIPT DI SPLITTING")
    print("--------------------------------------------------")
    
    TEST_LANG = "it"
    TEST_ID = "testpage"
    TEST_INPUT_FILE = os.path.join(OUTPUT_DIR, f"{TEST_LANG}_{TEST_ID}_maintext_INPUT.html")
    
    if not os.path.exists(TEST_INPUT_FILE):
        print(f"AVVISO: File di test richiesto: '{TEST_INPUT_FILE}' non trovato.")
        print("Crea un file HTML per eseguire il test. Saltato l'esecuzione.")
    else:
        split_and_update_content(TEST_INPUT_FILE, TEST_ID, TEST_LANG, CONFIG_JSON_FILE)
        print("Test completato. Controlla il file config.json per l'aggiornamento.")