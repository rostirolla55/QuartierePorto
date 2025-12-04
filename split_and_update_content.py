import os
import re
import json
from typing import Dict, Any

# =================================================================
# CONFIGURAZIONE GLOBALE
# =================================================================
# La cartella dove verranno salvati i file HTML splittati (es. text_files/it_cavaticcio_maintext1.html)
# NOTA: Questo è anche il percorso dove si aspetta di trovare il file di INPUT HTML.
OUTPUT_DIR = "text_files" 
# Marcatore usato nel file HTML di input per dividere il testo e associare un'immagine
# Formato nel file HTML: [SPLIT_BLOCK]nome_immagine.jpg;
SPLIT_MARKER = r"\[SPLIT_BLOCK\]"

# Le chiavi del JSON da aggiornare per i percorsi dei file HTML.
JSON_TEXT_KEYS = ["mainText1", "mainText2", "mainText3", "mainText4", "mainText5"]
# Le chiavi del JSON da aggiornare per i percorsi delle immagini.
JSON_IMAGE_KEYS = ["imageSource1", "imageSource2", "imageSource3", "imageSource4", "imageSource5"]

def load_json(filepath: str) -> Dict[str, Any] | None:
    """Carica il contenuto del file JSON di configurazione."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"\nERRORE FATALE: File di configurazione JSON non trovato: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"\nERRORE FATALE: Errore di decodifica JSON nel file: {filepath}")
        return None

def save_json(filepath: str, data: Dict[str, Any]):
    """Salva il contenuto aggiornato nel file JSON."""
    try:
        # Usa indent=4 per mantenere il file JSON leggibile e ensure_ascii=False per caratteri speciali
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✔️ CONFIGURAZIONE AGGIORNATA: File '{filepath}' salvato con successo.")
    except Exception as e:
        print(f"ERRORE: Impossibile salvare il file JSON aggiornato: {e}")

def split_and_update_content(input_filepath: str, base_id: str, lang: str, config_json_filepath: str):
    """
    Legge un file HTML di input, lo splitta, salva i blocchi, e aggiorna
    la pagina specifica nel file JSON di configurazione.
    """
    print(f"--- AVVIO PROCESSO PER PAGINA: {base_id} ({lang.upper()}) ---")
    
    # 1. Carica il JSON di configurazione
    config_data = load_json(config_json_filepath)
    if config_data is None:
        return
    
    # Verifica se l'ID della pagina esiste nel JSON
    if base_id not in config_data:
        print(f"\nERRORE: L'ID di pagina '{base_id}' non è stato trovato nel file JSON. Impossibile aggiornare.")
        return
        
    try:
        # Assicurati che la cartella di output (e di input, in questo caso) esista
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Carica il file HTML da splittare
        with open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
    except FileNotFoundError:
        print(f"\nERRORE: File di input HTML non trovato: {input_filepath}")
        return
    
    # Prepara il dizionario con gli aggiornamenti per la pagina corrente
    output_updates = {}
    
    # Pulisce mainText non splittato se si usano gli split block
    if "mainText" in config_data[base_id]:
        # Solo se è presente la chiave, la impostiamo a vuota per il caso in cui usiamo i blocchi
        output_updates["mainText"] = ""

    # Utilizza il marcatore per dividere il contenuto
    # La regex cattura il marcatore e il nome del file immagine, separandoli dal testo
    split_parts = re.split(f"({SPLIT_MARKER}.*?);", content, flags=re.IGNORECASE | re.DOTALL)
    
    # Rimuove il primo elemento se vuoto, utile se il marcatore inizia subito
    if not split_parts[0].strip() and len(split_parts) > 1:
        split_parts = split_parts[1:]

    current_text_index = 1
    
    # 2. Processa i blocchi di testo e i marcatori immagine
    for i in range(0, len(split_parts), 2):
        text_block = split_parts[i].strip()
        image_marker = ""

        if i + 1 < len(split_parts):
            image_marker = split_parts[i+1].strip()

        # Salta se il blocco di testo è vuoto (es. se c'è un doppio marcatore o spazi vuoti)
        if not text_block:
            continue

        # Genera il nome del file di output (es. it_cavaticcio_maintext1.html)
        output_filename = f"{lang}_{base_id}_maintext{current_text_index}.html"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)
        
        # Aggiorna la mappatura del testo
        if (current_text_index - 1) < len(JSON_TEXT_KEYS):
            json_key = JSON_TEXT_KEYS[current_text_index - 1]
            
            # 3. Salva il blocco di testo nel nuovo file
            try:
                with open(output_filepath, 'w', encoding='utf-8') as outfile:
                    outfile.write(text_block)
                print(f"  > Salvato blocco {current_text_index} in: {output_filepath}")
            except Exception as e:
                print(f"ERRORE SALVATAGGIO FILE {output_filepath}: {e}")
            
            output_updates[json_key] = output_filename
        else:
             print(f"AVVISO: Troppi blocchi di testo. Ignorato il blocco {current_text_index} (oltre i {len(JSON_TEXT_KEYS)} mainText).")

        # Estrai il nome dell'immagine e aggiorna la mappatura (usa l'indice del testo)
        if image_marker:
            # Rimuove il marcatore, pulisce spazi/newline/ecc. e il ";" finale
            image_name = image_marker.replace(SPLIT_MARKER, '').strip().rstrip(';')
            
            # *** PUNTO DI INTERVENTO: Conversione a minuscolo ***
            image_name_lower = image_name.lower()
            
            if (current_text_index - 1) < len(JSON_IMAGE_KEYS):
                json_img_key = JSON_IMAGE_KEYS[current_text_index - 1]
                # Usa il percorso relativo corretto per il JSON (es. cavaticcio/nomefile.jpg)
                image_path_json = f"{base_id}/{image_name_lower}"
                output_updates[json_img_key] = image_path_json
                print(f"  > Associata immagine a blocco {current_text_index}: {image_path_json} (Convertito a minuscolo)")
        
        current_text_index += 1

    # 4. Pulisce i campi non utilizzati con stringa vuota per coerenza
    # Si itera su tutti i possibili slot (da 1 a 5) e si puliscono quelli non usati
    blocks_processed = current_text_index - 1
    for i in range(len(JSON_TEXT_KEYS)):
        # Se l'indice (0-4) è maggiore o uguale al numero di blocchi effettivamente scritti (es. 2), pulisci
        if i >= blocks_processed: 
            output_updates[JSON_TEXT_KEYS[i]] = ""
            output_updates[JSON_IMAGE_KEYS[i]] = ""


    # 5. Aggiorna il JSON di configurazione
    
    # Sovrascrive o aggiunge le chiavi generate all'oggetto della pagina specifica
    config_data[base_id].update(output_updates)
    
    print("\n--- CAMPI AGGIORNATI NEL JSON ---")
    print(json.dumps(output_updates, indent=4, ensure_ascii=False)) # ensure_ascii=False per stampa
    print("---------------------------------")
    
    # 6. Salva il JSON modificato
    save_json(config_json_filepath, config_data)
    
    print(f"\nCOMPLETATO: Creati {blocks_processed} blocchi di testo/immagine processati.")


if __name__ == "__main__":
    # Esempio di utilizzo: Adatta questi tre parametri ogni volta che esegui lo script
    
    # 1. Il nome del file HTML di input con i marcatori [SPLIT_BLOCK]
    INPUT_FILE_NAME = "it_cavaticcio_maintext_INPUT.html" 
    
    # 2. L'ID della pagina da aggiornare nel file JSON (es. "cavaticcio", "pugliole", "graziaxx")
    BASE_PAGE_ID = "cavaticcio"                     
    
    # 3. La lingua (usata per i nomi dei file HTML creati: it_...)
    LANGUAGE = "it"                                 
    
    # Il percorso completo del file HTML di input (all'interno di 'text_files')
    INPUT_FILE_PATH = os.path.join(OUTPUT_DIR, INPUT_FILE_NAME)
    
    # PERCORSO DEL TUO texts.json (DA ADEGUARE!)
    # Se lo script è eseguito dalla cartella principale del progetto, usa il percorso corretto.
    CONFIG_JSON_FILE = "texts.json" 

    split_and_update_content(INPUT_FILE_PATH, BASE_PAGE_ID, LANGUAGE, CONFIG_JSON_FILE)