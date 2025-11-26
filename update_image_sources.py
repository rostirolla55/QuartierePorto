import json
import sys
import os

# Funzione helper per eseguire l'aggiornamento effettivo su un singolo file JSON
def _apply_update_to_json(json_path, page_id, update_data, lang_code):
    """Applica i dati dell'immagine a un singolo file texts.json per una data lingua."""
    try:
        # Leggi il contenuto JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Verifica se l'ID della pagina esiste
        if page_id not in data:
            # Stampa un avviso, non un errore fatale, in quanto la pagina potrebbe non esistere
            print(f"ATTENZIONE ({lang_code}): La pagina ID '{page_id}' non esiste in questo file JSON. Saltato l'aggiornamento.")
            return

        # Aggiorna le chiavi imageSource (imageSource1, imageSource2, ecc.)
        data[page_id].update(update_data)
        
        # Scrivi il contenuto JSON aggiornato
        with open(json_path, 'w', encoding='utf-8') as f:
            # Usiamo indent=4 per mantenere il JSON ben formattato e leggibile
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"SUCCESS ({lang_code}): Chiavi immagine aggiornate per '{page_id}' nel file JSON.")

    except FileNotFoundError:
        print(f"ERRORE ({lang_code}): File JSON non trovato al percorso: {json_path}")
    except json.JSONDecodeError as e:
        print(f"ERRORE ({lang_code}): Errore di sintassi JSON nel file: {e}")
    except Exception as e:
        print(f"ERRORE ({lang_code}) durante l'aggiornamento del JSON: {e}")


def update_image_sources(page_id, repo_root, image_filenames):
    """
    Aggiorna i percorsi delle immagini (imageSourceX) nel file texts.json
    per TUTTE le lingue disponibili, dato che le immagini sono cross-language.
    """

    translations_dir = os.path.join(repo_root, 'data', 'translations')
    
    # 1. Costruisci il dizionario di aggiornamento una sola volta (è lo stesso per tutte le lingue)
    update_data = {}
    for i, filename in enumerate(image_filenames):
        key = f"imageSource{i+1}"
        # Costruisce il percorso relativo corretto: [page_id]/[filename]
        update_data[key] = f"{page_id}/{filename}"
        
    print(f"Dati Immagine da scrivere: {update_data}")

    # 2. Trova tutte le cartelle lingua all'interno di data/translations
    try:
        languages = [d for d in os.listdir(translations_dir) if os.path.isdir(os.path.join(translations_dir, d))]
    except FileNotFoundError:
        print(f"ERRORE: Directory delle traduzioni non trovata al percorso: {translations_dir}. Impossibile procedere.")
        return

    print(f"Lingue trovate da aggiornare: {languages}")

    # 3. Aggiorna ogni file JSON per ogni lingua
    for lang_code in languages:
        json_path = os.path.join(translations_dir, lang_code, 'texts.json')
        _apply_update_to_json(json_path, page_id, update_data, lang_code)


if __name__ == "__main__":
    # Aggiornamento: Lo script ora accetta: [page_id] [repo_root] [lista_immagini...]
    
    if len(sys.argv) < 3:
        print("Uso: python update_image_sources.py <page_id> <repo_root> <immagine1.jpg> [immagine2.jpg] ...")
        print("Esempio: python update_image_sources.py pittoricarracci C:\\Users\\User\\Documents\\GitHub\\QuartierePorto grande_macelleria.jpg piccola_macelleria.jpg")
        sys.exit(1)

    page_id = sys.argv[1]
    repo_root = sys.argv[2]
    # Tutte le stringhe rimanenti sono i nomi dei file immagine
    image_filenames = sys.argv[3:] 

    update_image_sources(page_id, repo_root, image_filenames)