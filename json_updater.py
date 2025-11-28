import json
import sys
import os

def update_json_file(lang_code, key_path, input_txt_file):
    """
    Legge un file JSON, aggiorna un valore basandosi sul contenuto di un file .txt,
    e riscrive il JSON.

    Args:
        lang_code (str): Codice della lingua (es. 'it').
        key_path (str): Percorso della chiave da aggiornare (es. 'giangiorgi.mainText').
        input_txt_file (str): Percorso del file .txt da cui leggere il nuovo valore.
    """
    # Costruisci il percorso del file JSON (es. 'it/texts.json')
    json_path = os.path.join(lang_code, 'texts.json')
    
    # --- 1. Leggi il Contenuto Pulito dal file .txt ---
    try:
        with open(input_txt_file, 'r', encoding='utf-8') as f:
            new_value = f.read()
    except FileNotFoundError:
        print(f"ERRORE: File di input TXT non trovato: {input_txt_file}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERRORE durante la lettura del file TXT: {e}", file=sys.stderr)
        return False
        
    # --- 2. Leggi il File JSON Esistente ---
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERRORE: File JSON non trovato: {json_path}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"ERRORE: Il file JSON non è valido ({json_path}): {e}", file=sys.stderr)
        return False

    # --- 3. Aggiorna la Chiave ---
    keys = key_path.split('.')
    current_data = data
    
    try:
        # Naviga fino al livello precedente alla chiave finale
        for key in keys[:-1]:
            current_data = current_data[key]
            
        # Aggiorna il valore finale
        current_data[keys[-1]] = new_value
        
    except KeyError:
        print(f"ERRORE: Chiave non trovata nel JSON: {key_path}", file=sys.stderr)
        return False

    # --- 4. Scrivi il JSON Modificato ---
    try:
        # Usiamo indent=4 per rendere il JSON leggibile
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Stampa messaggio di successo troncato per il log del batch
        truncated_value = new_value[:60].replace('\n', ' ').strip()
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
        sys.exit(0)
    else:
        sys.exit(1)