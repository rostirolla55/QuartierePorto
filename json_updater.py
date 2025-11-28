import json
import sys
import os

def update_json_file(lang_code, key_path, input_txt_file):
    """
    Legge un file JSON, aggiorna un valore basandosi sul contenuto di un file .txt.
    Esegue la conversione cruciale: \n -> <br> per il testo puro.
    Include messaggi di debug.
    """
    # Costruisci il percorso del file JSON (es. 'it/texts.json')
    json_path = os.path.join(lang_code, 'texts.json')
    
    # --- 1. Leggi il Contenuto Pulito dal file .txt ---
    print(f"DEBUG: Tentativo di leggere il TXT da: {input_txt_file}")
    try:
        with open(input_txt_file, 'r', encoding='utf-8') as f:
            new_value = f.read()
    except FileNotFoundError:
        print(f"ERRORE: File di input TXT non trovato: {input_txt_file}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERRORE durante la lettura del file TXT: {e}", file=sys.stderr)
        return False
    
    # Stampa il valore RAW letto dal TXT (i \n sono veri a capo)
    print(f"DEBUG: Valore RAW letto dal TXT (prime 100 char):\n{new_value[:100]}")
        
    # --- 2. Conversione Cruciale: \n in <br> ---
    # Sostituiamo prima i doppi a capo (\n\n) con due <br> per un separatore di paragrafo, 
    # poi i singoli \n con un singolo <br>.
    html_ready_value = new_value.replace('\n\n', '<br><br>').replace('\n', '<br>').strip()

    # Stampa il valore pronto per l'HTML (dovrebbe contenere <br>)
    print(f"DEBUG: Valore PRONTO per HTML (dopo conversione):\n{html_ready_value}")
    
    # --- 3. Leggi il File JSON Esistente ---
    print(f"DEBUG: Tentativo di leggere il JSON da: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERRORE: File JSON non trovato: {json_path}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"ERRORE: Il file JSON non è valido ({json_path}): {e}", file=sys.stderr)
        return False

    # --- 4. Aggiorna la Chiave nell'oggetto Python ---
    keys = key_path.split('.')
    current_data = data
    
    try:
        for key in keys[:-1]:
            current_data = current_data[key]
            
        # Inserisci il valore pronto per l'HTML (con <br>)
        print(f"DEBUG: Aggiornamento chiave '{key_path}' con nuovo valore...")
        current_data[keys[-1]] = html_ready_value
        
    except KeyError:
        print(f"ERRORE: Chiave non trovata nel JSON: {key_path}", file=sys.stderr)
        return False

    # --- 5. Scrivi il JSON Modificato ---
    try:
        # Usiamo json.dump standard.
        print(f"DEBUG: Tentativo di scrittura del JSON modificato in: {json_path}")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Stampa messaggio di successo troncato per il log del batch
        truncated_value = html_ready_value[:60].replace('<br>', ' ').strip()
        print(f"✅ Aggiornato con successo: '{key_path}'. Valore finale (truncate): '{truncated_value}...'")
        return True
    
    except Exception as e:
        print(f"ERRORE durante la scrittura del file JSON: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python json_updater.py <lang_code> <key_path> <input_txt_file>", file=sys.stderr)
        sys.exit(1)
        
    lang_code = sys.argv[1]
    key_path = sys.argv[2]
    input_txt_file = sys.argv[3]
    
    if update_json_file(lang_code, key_path, input_txt_file):
        # Aggiungo un messaggio di conferma per il batch.
        print("Operazione completata. Controlla il file JSON")
        sys.exit(0)
    else:
        sys.exit(1)