import json
import sys
import os
import re

def update_json_file(lang_code, key_path, input_txt_file):
    """
    Legge un file JSON, aggiorna un valore basandosi sul contenuto di un file .txt.
    1. Esegue la pulizia aggressiva dei riferimenti immagine (anche se circondati da HTML o punti e virgola).
    2. Gestisce la conversione \n -> <br> SOLO per il testo puro.
    3. Utilizza i percorsi assoluti corretti (data/translations/lang).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, 'data', 'translations', lang_code, 'texts.json')
    
    # --- 1. Leggi il Contenuto Pulito dal file .txt ---
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
        
    # --- 2. PULIZIA AGGRESSIVA: Rimuovi i riferimenti a file immagine ---
    
    # Pattern: Cerca l'intera riga che contiene un riferimento a un'estensione immagine
    # e la rimuove completamente.
    pattern_to_remove_image_ref = re.compile(r'^.*?\.(jpg|png|gif|jpeg|svg).*$', re.IGNORECASE | re.MULTILINE)
    
    # Sostituiamo le righe contenenti il riferimento all'immagine con una stringa vuota ('')
    cleaned_value = pattern_to_remove_image_ref.sub('', new_value)
    
    # Pulizia degli a capo superflui lasciati dalla rimozione
    cleaned_value = re.sub(r'\n{2,}', '\n\n', cleaned_value)

    print(f"DEBUG: Valore dopo la pulizia immagine (prime 100 char):\n{cleaned_value[:100].replace('\n', '\\n')}")

    # --- 3. Conversione Cruciale: \n in <br> (SOLO per testo non HTML) ---
    
    html_ready_value = cleaned_value.strip()

    # Controlla se il contenuto è HTML (contiene tag noti come <p>, <img>, ecc.)
    if not re.search(r'<[a-z/][^>]*>', html_ready_value):
        print("DEBUG: Conversione: Applica \n -> <br> (Contenuto non HTML)")
        html_ready_value = html_ready_value.replace('\n\n', '<br><br>')
        html_ready_value = html_ready_value.replace('\n', '<br>').strip()
    else:
        # Se è HTML, normalizziamo solo gli a capo per non interferire con la formattazione
        print("DEBUG: Conversione: Mantiene HTML (Normalizza a capo)")
        html_ready_value = html_ready_value.replace('\n', ' ').strip()
    
    print(f"DEBUG: Valore PRONTO per JSON:\n{html_ready_value}")

    # --- 4. Leggi e Aggiorna il File JSON ---
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

    # Aggiorna e Scrivi
    keys = key_path.split('.')
    current_data = data
    
    try:
        for key in keys[:-1]:
            current_data = current_data[key]
            
        current_data[keys[-1]] = html_ready_value
        print(f"DEBUG: Aggiornamento chiave '{key_path}' con nuovo valore OK.")

        print(f"DEBUG: Tentativo di scrittura del JSON modificato in: {json_path}")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Log di successo
        truncated_value = html_ready_value[:60].replace('<br>', ' ').strip()
        print(f"✅ Aggiornato con successo: '{key_path}'. Contenuto: '{truncated_value}...'")
        return True
    
    except KeyError:
        print(f"ERRORE: Chiave non trovata nel JSON: {key_path}", file=sys.stderr)
        return False
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