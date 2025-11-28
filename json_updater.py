import json
import sys
import os

def update_json_file(lang_code, key_path, input_txt_file):
    """
    Legge un file JSON, aggiorna un valore basandosi sul contenuto di un file .txt.
    Esegue la conversione cruciale: \n -> <br> per il testo puro.
    Utilizza i percorsi assoluti corretti (data/translations/lang).
    """
    # Ottiene la directory dello script Python.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Costruisce il percorso ASSOLUTO del file JSON usando la struttura corretta
    # {script_dir}/data/translations/{lang_code}/texts.json
    json_path = os.path.join(script_dir, 'data', 'translations', lang_code, 'texts.json')
    
    # --- 1. Leggi il Contenuto Pulito dal file .txt ---
    # Costruisce il percorso completo del file TXT
    full_txt_path = os.path.join(script_dir, input_txt_file) 
    
    print(f"DEBUG: Tentativo di leggere il TXT da: {full_txt_path}")
    try:
        with open(full_txt_path, 'r', encoding='utf-8') as f:
            new_value = f.read()
    except FileNotFoundError:
        print(f"ERRORE: File di input TXT non trovato: {full_txt_path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERRORE durante la lettura del file TXT: {e}", file=sys.stderr)
        return False
        
    print(f"DEBUG: Valore RAW letto dal TXT (prime 100 char):\n{new_value[:100].replace('\n', '\\n')}")
        
    # --- 2. Conversione Cruciale: \n in <br> ---
    # Sostituiamo i doppi a capo con <br><br> (separatore di paragrafo) e i singoli a capo con <br>.
    html_ready_value = new_value.replace('\n\n', '<br><br>').replace('\n', '<br>').strip()
    
    print(f"DEBUG: Valore PRONTO per HTML (dopo conversione):\n{html_ready_value}")

    # --- 3. Leggi il File JSON Esistente ---
    print(f"DEBUG: Tentativo di leggere il JSON da: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERRORE: File JSON non trovato. Verifica il percorso: {json_path}", file=sys.stderr)
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
            
        current_data[keys[-1]] = html_ready_value
        print(f"DEBUG: Aggiornamento chiave '{key_path}' con nuovo valore OK.")
        
    except KeyError:
        print(f"ERRORE: Chiave non trovata nel JSON: {key_path}", file=sys.stderr)
        return False

    # --- 5. Scrivi il JSON Modificato (usando standard JSON.dump) ---
    try:
        print(f"DEBUG: Tentativo di scrittura del JSON modificato in: {json_path}")
        with open(json_path, 'w', encoding='utf-8') as f:
            # Usando json.dump, si assicura che il formato sia valido, e poiché non ci sono
            # più \n nel valore, non avrai più il problema del doppio escape (\\n).
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Log di successo
        truncated_value = html_ready_value[:60].replace('<br>', ' ').strip()
        print(f"✅ Aggiornato con successo: '{key_path}'. Contenuto: '{truncated_value}...'")
        return True
    
    except Exception as e:
        print(f"ERRORE durante la scrittura del file JSON: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
        
    lang_code = sys.argv[1]
    key_path = sys.argv[2]
    input_txt_file = sys.argv[3]
    
    if update_json_file(lang_code, key_path, input_txt_file):
        print("Operazione completata. Controlla il file JSON.")
        sys.exit(0)
    else:
        print("ERRORE: L'aggiornamento della chiave JSON e' fallito.")
        sys.exit(1)