import os
import re
import json
from bs4 import BeautifulSoup

def update_html_from_json():
    """
    Aggiorna i file HTML ripristinando la struttura corretta del menu:
    <nav id="navBarMain"> -> <div class="nav-bar-content"> -> <ul>
    """
    # Directory principale (dove si trovano gli HTML)
    root_path = os.getcwd()
    # Directory dove si trovano i file JSON
    json_folder = os.path.join(root_path, "menu_json")
    
    # Pattern per identificare la lingua dal nome del file (es. index-en.html -> en)
    lang_pattern = re.compile(r'-([a-z]{2})\.html$')
    
    # Verifica che la cartella dei JSON esista
    if not os.path.exists(json_folder):
        print(f"Errore: La cartella '{json_folder}' non esiste.")
        return

    # 1. Caricamento dei JSON dalla cartella menu_json
    menu_data = {}
    json_files = [f for f in os.listdir(json_folder) if f.startswith("nav-") and f.endswith(".json")]
    
    if not json_files:
        print(f"Errore: Nessun file nav-xx.json trovato in '{json_folder}'.")
        return

    for jf_name in json_files:
        # Estrae il codice lingua (es. da nav-en.json estrae en)
        lang_code = jf_name.replace("nav-", "").replace(".json", "")
        try:
            with open(os.path.join(json_folder, jf_name), 'r', encoding='utf-8') as jf:
                menu_data[lang_code] = json.load(jf)
                print(f"Configurazione caricata per: {lang_code}")
        except Exception as e:
            print(f"Errore nel caricamento di {jf_name}: {e}")

    # 2. Aggiornamento dei file HTML nella root
    html_files = [f for f in os.listdir(root_path) if f.endswith(".html")]
    
    if not html_files:
        print("Nessun file HTML trovato nella directory corrente.")
        return

    for html_name in html_files:
        # Determina la lingua (default 'it' se non trova il suffisso -xx)
        match = lang_pattern.search(html_name)
        lang = match.group(1) if match else "it"
        
        if lang not in menu_data:
            print(f"Salto {html_name}: nessuna configurazione JSON per la lingua '{lang}'")
            continue
            
        file_path = os.path.join(root_path, html_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
            
            nav_tag = soup.find('nav', id='navBarMain')
            
            if nav_tag:
                # Sostituiamo il contenuto del tag nav
                nav_tag.clear()
                
                # 1. Creiamo il div intermedio 'nav-bar-content'
                nav_content_div = soup.new_tag('div', attrs={'class': 'nav-bar-content'})
                
                # 2. Creiamo la lista ul (rimossa la classe 'nav-list' per tornare all'originale)
                ul = soup.new_tag('ul')
                
                for item in menu_data[lang].get('items', []):
                    li = soup.new_tag('li')
                    a = soup.new_tag('a', href=item['href'])
                    if 'id' in item:
                        a['id'] = item['id']
                    a.string = item['text']
                    li.append(a)
                    ul.append(li)
                
                # Assemblaggio della struttura: nav -> div -> ul
                nav_content_div.append(ul)
                nav_tag.append(nav_content_div)
                
                # Scrittura su file
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Usiamo formatter=None per evitare l'encoding delle entità HTML se necessario
                    f.write(soup.prettify(formatter="html"))
                print(f"OK: {html_name} aggiornato con la struttura corretta.")
            else:
                print(f"AVVISO: {html_name} non contiene <nav id='navBarMain'>")
                
        except Exception as e:
            print(f"Errore durante l'elaborazione di {html_name}: {e}")

if __name__ == "__main__":
    print("Inizio aggiornamento automatico menu (versione layout originale)...")
    update_html_from_json()
    print("\nProcedura completata.")