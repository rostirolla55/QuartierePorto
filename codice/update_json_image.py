import json
import sys
import os

# Definisci il percorso base dei file JSON di traduzione
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(REPO_ROOT, "data", "translations")

# Lista delle lingue supportate
LANGUAGES = ["it", "en", "es", "fr"]

def update_image_sources(page_id, image_files):
    """
    Aggiorna i campi imageSource per la pagina specificata in tutti i file JSON.
    :param page_id: L'ID della pagina (es. 'arcoxy').
    :param image_files: Lista di nomi di file immagine (massimo 5).
    """
    print(f"Aggiornamento di {len(image_files)} immagini per la pagina: {page_id}")
    
    # Prepara il dizionario dei percorsi immagine
    image_data = {}
    for i in range(1, 6):
        key = f"imageSource{i}"
        # Assegna il nome del file se presente, altrimenti stringa vuota
        if i <= len(image_files):
            image_data[key] = image_files[i-1]
        else:
            image_data[key] = ""

    # Itera su tutte le lingue
    for lang in LANGUAGES:
        json_file_path = os.path.join(DATA_PATH, lang, "texts.json")
        
        if not os.path.exists(json_file_path):
            print(f"ERRORE: File JSON non trovato per {lang}: {json_file_path}", file=sys.stderr)
            continue

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"ERRORE di lettura JSON per {lang}: {e}", file=sys.stderr)
            continue

        # --- Logica di Aggiornamento ---
        # Si aspetta che i dati siano un dizionario dove la chiave è l'ID della pagina
        if page_id in data:
            print(f"  > Aggiornamento JSON {lang}/texts.json...")
            
            # Aggiorna i campi imageSource1 a imageSource5
            for key, value in image_data.items():
                data[page_id][key] = value
            
            # Scrivi il file JSON aggiornato
            try:
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                print(f"  > Successo: {lang} aggiornato.")
            except Exception as e:
                print(f"ERRORE di scrittura JSON per {lang}: {e}", file=sys.stderr)
        else:
            print(f"ATTENZIONE: ID Pagina '{page_id}' non trovato in {lang}/texts.json. Saltato.", file=sys.stderr)


if __name__ == '__main__':
    # Il primo argomento è il nome dello script, quindi i dati iniziano da sys.argv[1]
    # sys.argv[1] = page_id
    # sys.argv[2:] = image_files (lista di nomi di file)
    
    if len(sys.argv) < 2:
        print("Uso: python update_json_image.py <id_pagina> <file_img_1> [file_img_2...]", file=sys.stderr)
        sys.exit(1)
        
    page_id = sys.argv[1]
    image_files = sys.argv[2:]
    
    # Limita a 5 immagini come definito nel tuo workflow
    if len(image_files) > 5:
        print("ATTENZIONE: Hai fornito più di 5 immagini. Saranno usate solo le prime 5.", file=sys.stderr)
        image_files = image_files[:5]
        
    update_image_sources(page_id, image_files)
    sys.exit(0)