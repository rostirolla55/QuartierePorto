import sys
import os
import json
import datetime
import shutil 
import re 

# --- CONFIGURAZIONI GLOBALI ---
LANGUAGES = ['it', 'en', 'es', 'fr']
NAV_MARKER = '// ** MARKER: START NEW NAV LINKS **' # Marcatore per main.js
POI_MARKER = '// ** MARKER: START NEW POIS **'      # Marcatore per main.js
HTML_NAV_MARKER = '</ul>'                           # Marcatore per i file HTML: USIAMO </ul> per INSERIRE IN FONDO
HTML_TEMPLATE_NAME = 'template-it.html'             # Nome del file HTML da usare come template

# ----------------------------------------------------------------------------------

def get_translations_for_nav(page_title_it):
    """
    Ritorna le traduzioni hardcoded per il link di navigazione.
    """
    print("ATTENZIONE: Stiamo usando traduzioni placeholder per il menu. AGGIORNARE manualemnte se necessario.")
    return {
        'it': page_title_it,
        'en': 'Ex Tobacco Factory',
        'es': 'Ex Fabrica de Tabaco',
        'fr': 'Ancienne Manufacture de Tabac'
    }

def update_main_js(repo_root, page_id, nav_key_id, lat, lon, distance):
    """Aggiorna POIS_LOCATIONS e navLinksData in main.js."""
    js_path = os.path.join(repo_root, 'main.js')
    
    # Linee da iniettare: rimosso eccesso di a capo per evitare righe vuote
    new_poi = f"    {{ id: '{page_id}', lat: {lat}, lon: {lon}, distanceThreshold: {distance} }},"
    new_nav = f"    {{ id: '{nav_key_id}', key: '{nav_key_id}', base: '{page_id}' }},"
    
    # Le linee saranno inserite prima del marker, mantenendo la formattazione pulita
    new_poi_injection = new_poi + '\n' + POI_MARKER
    new_nav_injection = new_nav + '\n' + NAV_MARKER
    
    try:
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Inserimento POI (Invertito il marcatore per inserire in cima alla lista)
        if POI_MARKER in content:
            content = content.replace(POI_MARKER, new_poi_injection)
            print(f"✅ Inserito POI in main.js")
        else:
            print(f"⚠️ ATTENZIONE: Marcatore POI non trovato: '{POI_MARKER}'")

        # Inserimento NAV LINK DATA (Invertito il marcatore per inserire in cima alla lista)
        if NAV_MARKER in content:
            content = content.replace(NAV_MARKER, new_nav_injection)
            print(f"✅ Inserito navLinksData in main.js")
        else:
            print(f"⚠️ ATTENZIONE: Marcatore NavLinks non trovato: '{NAV_MARKER}'")
            
        with open(js_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"ERRORE aggiornando main.js: {e}")

def update_texts_json_nav(repo_root, page_id, nav_key_id, translations):
    """Aggiorna il blocco nav e inizializza il blocco della pagina con tutte le chiavi (SCHEMA COMPLETO)."""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # SCHEMA COMPLETO (tutte le chiavi inizializzate)
    NEW_PAGE_SCHEMA = {
        "pageTitle": "", 
        "mainText": "",
        "mainText1": "",
        "mainText2": "",
        "mainText3": "",
        "mainText4": "",
        "mainText5": "",
        "playAudioButton": "Ascolta con le cuffie", 
        "pauseAudioButton": "Pausa",               
        "imageSource1": "",
        "imageSource2": "",
        "imageSource3": "",
        "imageSource4": "",
        "imageSource5": "",
        "sourceText": "",
        "creationDate": current_date,
        "lastUpdate": current_date,
        "audioSource": "" 
    }
    
    for lang in LANGUAGES:
        json_path = os.path.join(repo_root, 'data', 'translations', lang, 'texts.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 1. Aggiorna il blocco 'nav'
            data['nav'][nav_key_id] = translations[lang]

            # 2. Inizializza/Aggiorna il blocco della pagina
            if page_id not in data:
                # Creazione del blocco per la nuova pagina (Schema completo)
                new_block = NEW_PAGE_SCHEMA.copy()
                new_block['pageTitle'] = translations[lang]
                new_block['audioSource'] = f"Assets/Audio/{lang}/{page_id}.mp3"
                
                # Aggiungi un placeholder per il testo iniziale
                if lang == 'it' or lang == 'en':
                    new_block['mainText'] = "Testo iniziale per la traduzione."
                
                data[page_id] = new_block
                print(f"✅ Inizializzato NUOVO blocco '{page_id}' in {lang}/texts.json con schema completo.")
            else:
                # Se la pagina esiste, aggiorna date e assicurati che abbia tutte le chiavi richieste
                for key, default_value in NEW_PAGE_SCHEMA.items():
                    if key not in data[page_id]:
                        data[page_id][key] = default_value
                        
                data[page_id]['lastUpdate'] = current_date
                
                # Correggi il titolo: elimina 'title' se presente e usa 'pageTitle'
                if 'title' in data[page_id]:
                    del data[page_id]['title'] 
                data[page_id]['pageTitle'] = translations[lang]
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Aggiornato nav e schema in {lang}/texts.json")
            
        except FileNotFoundError:
            print(f"ERRORE: File JSON non trovato per la lingua {lang}.")
        except Exception as e:
            print(f"ERRORE aggiornando JSON per {lang}: {e}")

def get_target_lang_code(filename):
    """Determina il codice linguistico corretto dal nome del file HTML."""
    parts = filename.split('-')
    if len(parts) > 1:
        # File con suffisso: es. index-en.html -> 'en'
        return parts[-1].replace(".html", "")
    else:
        # File senza suffisso: es. index.html -> 'it' (presumendo lingua di default)
        return 'it'

def update_html_files(repo_root, page_id, nav_key_id, translations, page_title_it):
    """
    Crea i nuovi file HTML dal template, aggiorna il menu e il Cache Busting
    in TUTTI i file HTML esistenti.
    """
    
    MARKER = HTML_NAV_MARKER # Il tag </ul> è il marcatore
    
    all_html_files = [
        os.path.join(repo_root, f) 
        for f in os.listdir(repo_root) 
        if f.endswith('.html')
    ]
    today_version = datetime.datetime.now().strftime("%Y%m%d_%H%M") 

    for existing_path in all_html_files:
        try:
            filename = os.path.basename(existing_path)
            target_lang = get_target_lang_code(filename) # Determina la lingua del file corrente
            
            # --- PARTE A: GESTIONE CREAZIONE NUOVO FILE ---
            if filename == HTML_TEMPLATE_NAME:
                # Salta la creazione qui, si passa direttamente all'aggiornamento
                pass 
            else:
                new_page_filename = f'{page_id}-{target_lang}.html'
                new_page_path = os.path.join(repo_root, new_page_filename)

                if target_lang in LANGUAGES and not os.path.exists(new_page_path):
                    template_path = os.path.join(repo_root, HTML_TEMPLATE_NAME)
                    if os.path.exists(template_path):
                        # Copia dal template
                        shutil.copyfile(template_path, new_page_path)
                        
                        # Aggiorna il tag <body> id e i link interni nel nuovo file
                        with open(new_page_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Aggiorna l'ID del body della nuova pagina
                        content = content.replace('id="template"', f'id="{page_id}"')
                        
                        with open(new_page_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"✅ Creato nuovo file: {new_page_filename}")
                    else:
                        print(f"ERRORE: Template HTML non trovato: {HTML_TEMPLATE_NAME}")


            # --- PARTE B: AGGIORNAMENTO NAVIGAZIONE E CACHE ---
            
            with open(existing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Link da iniettare: PUNTA ALLA PAGINA NUOVA NELLA LINGUA DEL FILE CORRENTE
            nav_link_to_insert = (
                f'        <li><a id="{nav_key_id}" href="{page_id}-{target_lang}.html">'
                f'{translations.get(target_lang, page_title_it)}</a></li>'
            )
            
            # Iniezione del link nel menu: SOSTITUIAMO </ul> con [NUOVO LINK] + </ul>
            # Questo mette il link in fondo alla lista
            injection_string = nav_link_to_insert + '\n        ' + MARKER
            
            # Se la riga del link non è già presente E troviamo il marcatore </ul>
            if MARKER in content and nav_link_to_insert not in content:
                content = content.replace(MARKER, injection_string)
                print(f"✅ Aggiunto link a {filename} (in fondo, link corretto: {page_id}-{target_lang}.html)")
                
            # 2. Aggiornamento Cache Busting
            content = re.sub(r'main\.js\?v=([0-9A-Z_]*)', f'main.js?v={today_version}', content)
            
            with open(existing_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Aggiornato cache in {filename}")

        except Exception as e:
            print(f"ERRORE aggiornando HTML: {filename}: {e}")

def main():
    if len(sys.argv) != 8:
        print("Uso: python add_page.py <page_id> <nav_key_id> <page_title_it> <lat> <lon> <distance> <repo_root>")
        sys.exit(1)

    page_id = sys.argv[1]
    nav_key_id = sys.argv[2]
    page_title_it = sys.argv[3]
    lat = sys.argv[4]
    lon = sys.argv[5]
    distance = sys.argv[6]
    repo_root = sys.argv[7]
    
    # 1. Recupero traduzioni per la navigazione
    translations = get_translations_for_nav(page_title_it)

    print("\n--- AGGIORNAMENTO JSON ---")
    update_texts_json_nav(repo_root, page_id, nav_key_id, translations)
    
    print("\n--- AGGIORNAMENTO MAIN.JS ---")
    update_main_js(repo_root, page_id, nav_key_id, lat, lon, distance)

    print("\n--- AGGIORNAMENTO HTML E CREAZIONE NUOVE PAGINE ---")
    update_html_files(repo_root, page_id, nav_key_id, translations, page_title_it)

if __name__ == "__main__":
    main()