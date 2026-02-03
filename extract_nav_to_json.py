import os
import re
import json
from bs4 import BeautifulSoup

def extract_nav_to_json(root_directory, output_directory="menu_json"):
    """
    Scansiona i file HTML, estrae il menu navBarMain e genera file JSON per lingua.
    """
    # Pattern per identificare la lingua dal nome del file (es. "-en", "-fr")
    # Se non trova suffissi, assume "it"
    lang_pattern = re.compile(r'-([a-z]{2})\.html$')
    
    # Dizionario per raggruppare i menu per lingua { 'en': [...items...], 'it': [...] }
    translations = {}

    # Crea la cartella di output se non esiste
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    print(f"Inizio scansione nella cartella: {root_directory}")

    for filename in os.listdir(root_directory):
        if filename.endswith(".html"):
            file_path = os.path.join(root_directory, filename)
            
            # Determina la lingua
            match = lang_pattern.search(filename)
            lang_code = match.group(1) if match else "it"

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f, 'html.parser')

                # Cerca il tag nav con l'ID specifico
                nav_tag = soup.find('nav', id='navBarMain')
                
                if nav_tag:
                    items = []
                    # Trova tutti i link dentro i list item
                    links = nav_tag.find_all('a')
                    
                    for link in links:
                        item = {
                            "id": link.get('id', ''),
                            "href": link.get('href', '#'),
                            "text": link.get_text(strip=True)
                        }
                        items.append(item)

                    # Se abbiamo trovato dei link e non abbiamo ancora salvato questa lingua
                    # (o vogliamo sovrascrivere con l'ultima versione trovata)
                    if items:
                        translations[lang_code] = {"items": items}
                        print(f"Estratto menu ({lang_code}) da: {filename}")
                
            except Exception as e:
                print(f"Errore durante l'elaborazione di {filename}: {e}")

    # Generazione dei file JSON
    for lang, data in translations.items():
        output_file = os.path.join(output_directory, f"nav-{lang}.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as jf:
                json.dump(data, jf, ensure_ascii=False, indent=4)
            print(f"File generato con successo: {output_file}")
        except Exception as e:
            print(f"Errore nel salvataggio del JSON per {lang}: {e}")

if __name__ == "__main__":
    # Assicurati di aver installato beautifulsoup4: pip install beautifulsoup4
    # Esegue lo script nella cartella corrente
    extract_nav_to_json(".")