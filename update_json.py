import sys
import os
import json
import datetime

# --- CONFIGURAZIONI GLOBALI ---
LANGUAGES = ['it', 'en', 'es', 'fr']
# ------------------------------

def update_json_file(repo_root, page_id, key_id, language, text_file_path):
    """
    Aggiorna il valore di una singola chiave (key_id) per una specifica pagina (page_id)
    in un determinato file texts.json (specificato da language), leggendo il nuovo testo 
    da un file esterno.
    """
    
    # Costruisci il percorso del file JSON specifico (es. .../data/translations/it/texts.json)
    json_path = os.path.join(repo_root, 'data', 'translations', language, 'texts.json')
    
    try:
        # 1. Leggi il nuovo contenuto dal file di testo
        with open(text_file_path, 'r', encoding='utf-8') as f:
            new_text_content = f.read().strip()
            
        print(f"Letto nuovo testo per la chiave '{key_id}' nella lingua '{language}'.")

        # 2. Carica il file JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 3. Verifica e Aggiorna il testo e la data
        if page_id not in data:
            print(f"ERRORE: La pagina '{page_id}' non esiste in {language}/texts.json.")
            return

        if key_id not in data[page_id]:
            print(f"ERRORE: La chiave '{key_id}' non esiste nella pagina '{page_id}' in {language}/texts.json.")
            return
            
        # Aggiorna il testo
        data[page_id][key_id] = new_text_content
        
        # Aggiorna la data di modifica (opzionale, ma consigliato)
        data[page_id]['lastUpdate'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Scrivi il JSON modificato
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Aggiornamento completato: Chiave '{key_id}' in {language}/texts.json.")
            
    except FileNotFoundError:
        print(f"ERRORE: File JSON non trovato per la lingua {language}, o file di testo non trovato: {text_file_path}")
    except Exception as e:
        print(f"ERRORE durante l'aggiornamento del JSON: {e}")

# ----------------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Uso: python update_json.py <repo_root> <page_id> <key_id> <language> <text_file_path>")
        print("Esempio: python update_json.py . manifattura mainText it ./texts/manifattura-it-mainText.txt")
        sys.exit(1)

    repo_root = sys.argv[1]
    page_id = sys.argv[2]
    key_id = sys.argv[3]
    language = sys.argv[4]
    text_file_path = sys.argv[5]
    
    update_json_file(repo_root, page_id, key_id, language, text_file_path)