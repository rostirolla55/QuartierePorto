import os
import re
import subprocess
import shutil
from typing import Tuple, Optional

# Importa le costanti e la funzione di splitting dal file 'split_and_update_content.py'.
# ASSICURATI che 'split_and_update_content.py' sia nella stessa cartella.
try:
    # CONFIG_JSON_FILE e OUTPUT_DIR sono importate da split_and_update_content.py
    from split_and_update_content import split_and_update_content, OUTPUT_DIR, CONFIG_JSON_FILE
except ImportError:
    print("ERRORE: Impossibile importare 'split_and_update_content.py'. Assicurati che il file sia nella stessa directory.")
    # Esci in caso di errore di importazione critico
    exit(1)

# =================================================================
# CONFIGURAZIONE UTENTE
# =================================================================

# 1. Percorso ASSOLUTO dell'eseguibile di LibreOffice (soffice.exe)
# Questo strumento è preferito per l'automazione perché supporta l'opzione '--headless'.
# NOTA: Devi sostituire il percorso qui sotto con quello REALE del tuo eseguibile soffice.exe!
# Esempio per Windows: r"C:\Program Files\LibreOffice\program\soffice.exe"
# Esempio per Linux: "/usr/bin/libreoffice"
SOFFICE_TOOL_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe" 

# =================================================================

def extract_metadata(filename: str) -> Optional[Tuple[str, str]]:
    """Estrae la lingua (lang) e l'ID della pagina (page_id) dal nome del file."""
    # Pattern: [lang]-[pageID].docx (es. it-cavaticcio.docx)
    match = re.match(r"(\w{2})-([\w-]+)\.docx$", filename, re.IGNORECASE)
    if match:
        lang = match.group(1).lower()
        page_id = match.group(2).lower()
        return lang, page_id
    return None

def word_to_html_converter(docx_path: str, html_output_path: str) -> bool:
    """
    Esegue la conversione DOCX -> HTML utilizzando LibreOffice in modalità headless.
    """
    print(f"\n--- PASSO 1: CONVERSIONE DOCX -> HTML per: {os.path.basename(docx_path)} ---")
    
    # La directory di output è la stessa di OUTPUT_DIR (cioè 'text_files')
    output_dir = os.path.dirname(html_output_path)
    # Estrai il nome del file DOCX senza estensione (es. 'it-cavaticcio')
    base_name_only = os.path.splitext(os.path.basename(docx_path))[0]
    
    # 1. LibreOffice crea un file nella cartella di output con lo stesso nome del DOCX ma estensione .html
    expected_output_filename = f"{base_name_only}.html"
    generated_path = os.path.join(output_dir, expected_output_filename)
    
    # 2. Definizione degli argomenti per LibreOffice
    command = [
        SOFFICE_TOOL_PATH, 
        '--headless', # Esegue senza interfaccia grafica
        '--convert-to', 'html', # Specifica il formato di output
        docx_path, # Il file da convertire
        '--outdir', output_dir # La directory dove salvare l'output
    ]
    
    # Rimuovi eventuali file HTML generati in precedenza con lo stesso nome
    if os.path.exists(generated_path):
        os.remove(generated_path)
    
    try:
        # 3. Esecuzione del comando
        print(f"Esecuzione: {' '.join(command)}")
        # Il parametro check=True solleva un errore se il processo termina con un codice non zero
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        
        # 4. Rinomina il file generato (es. it-cavaticcio.html) nel formato atteso dallo splitter
        # Il formato atteso è lang_pageid_maintext_INPUT.html
        if os.path.exists(generated_path):
            # A volte LibreOffice aggiunge un nome al file generato, ma in questo setup base, 
            # dovrebbe essere il nome base del DOCX.
            shutil.move(generated_path, html_output_path)
            print(f"Conversione RIUSCITA. File salvato in: {html_output_path}")
            return True
        else:
            print(f"ERRORE: LibreOffice non ha prodotto il file atteso: {generated_path}")
            print("Verifica i permessi di scrittura o il contenuto del file DOCX.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"ERRORE CONVERSIONE (Processo fallito): Lo strumento ha fallito con il codice {e.returncode}.")
        print(f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"ERRORE CRITICO (File non trovato): L'eseguibile di LibreOffice '{SOFFICE_TOOL_PATH}' non è stato trovato.")
        print("PER FAVORE: Aggiorna la variabile SOFFICE_TOOL_PATH con il percorso corretto.")
        return False
    except Exception as e:
        print(f"ERRORE generico durante la conversione/spostamento: {e}")
        return False


def process_all_pages():
    """
    Trova tutti i file DOCX, li converte in HTML e poi aggiorna il JSON
    tramite lo script di splitting.
    """
    # Assicurati che la directory OUTPUT_DIR esista
    if not os.path.exists(OUTPUT_DIR):
        print(f"Creazione della directory di output: {OUTPUT_DIR}")
        os.makedirs(OUTPUT_DIR)
        
    # Trova tutti i file .docx nella directory di output ('text_files')
    docx_files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.docx')]
    
    if not docx_files:
        print(f"AVVISO: Nessun file '.docx' trovato nella cartella '{OUTPUT_DIR}'. Nulla da processare.")
        return

    print(f"Trovati {len(docx_files)} file DOCX da processare...")
    
    total_processed = 0

    for docx_filename in docx_files:
        metadata = extract_metadata(docx_filename)
        if not metadata:
            print(f"AVVISO: Nome file non valido '{docx_filename}' (formato atteso: 'xx-nomepagina.docx'). Saltato.")
            continue
        
        lang, base_id = metadata
        docx_filepath = os.path.join(OUTPUT_DIR, docx_filename)
        
        # 1. Definizione del nome del file HTML di input atteso dallo script di split
        # Esempio: it_cavaticcio_maintext_INPUT.html
        html_input_filename = f"{lang}_{base_id}_maintext_INPUT.html"
        html_input_filepath = os.path.join(OUTPUT_DIR, html_input_filename)
        
        print(f"\n==================================================================")
        print(f"PAGINA: {base_id} ({lang.upper()}) | File DOCX: {docx_filename}")
        print(f"==================================================================")
        
        # --- PASSO 1: CONVERSIONE DOCX -> HTML (usa LibreOffice) ---
        conversion_success = word_to_html_converter(docx_filepath, html_input_filepath)
        
        if not conversion_success:
            print(f"SKIP: Conversione fallita per '{docx_filename}'. Passaggio alla pagina successiva.")
            continue
            
        # --- PASSO 2: SPLITTING E AGGIORNAMENTO JSON ---
        print(f"\n--- PASSO 2: SPLIT HTML e AGGIORNAMENTO JSON ---")
        try:
            # Chiama la funzione di splitting importata da split_and_update_content.py
            split_and_update_content(html_input_filepath, base_id, lang, CONFIG_JSON_FILE)
            total_processed += 1
            print(f"AGGIORNAMENTO RIUSCITO per {base_id} ({lang.upper()}).")
        except Exception as e:
            print(f"ERRORE CRITICO NELLO SPLIT per {docx_filename}: {e}")
            
        print(f"------------------------------------------------------------------")

    print("\n==================================================================")
    print(f"PROCESSO COMPLETO. {total_processed} pagine aggiornate con successo.")
    print(f"Verifica il file '{CONFIG_JSON_FILE}' e la cartella '{OUTPUT_DIR}'.")
    print("==================================================================")


if __name__ == "__main__":
    process_all_pages()