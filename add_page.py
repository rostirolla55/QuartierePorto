import sys
import os
import json
import datetime
import shutil
import re

# --- CONFIGURAZIONI GLOBALI ---
LANGUAGES = ['it', 'en', 'es', 'fr']
NAV_MARKER = '// ** MARKER: START NEW NAV LINKS **' # Marcatore per main.js
POI_MARKER = '// ** MARKER: START NEW POIS **' # Marcatore per main.js
HTML_NAV_MARKER = '</ul>' # Marcatore per i file HTML: USIAMO </ul> per INSERIRE IN FONDO
HTML_TEMPLATE_NAME = 'template-it.html' # Nome del file HTML da usare come template

# NUOVO MARCATORE PER IL CAMBIO LINGUA
LANGUAGE_SWITCHER_MARKER = '<!-- LANGUAGE_SWITCHER_PLACEHOLDER -->'
LANGUAGE_NAMES = {'it': 'Italiano', 'en': 'English', 'es': 'Español', 'fr': 'Français'}

# ----------------------------------------------------------------------------------

def get_translations_for_nav(page_title_it):
    """
    Ritorna le traduzioni hardcoded per il link di navigazione.
    """
    print("ATTENZIONE: Stiamo usando traduzioni placeholder per il menu. AGGIORNARE manualemnte se necessario.")
    return {
        'it': page_title_it,
        'en': 'The Carracci Painters', # Traduzione placeholder EN (Regolare se necessario)
        'es': 'Los Pintores Carracci', # Traduzione placeholder ES (Regolare se necessario)
        'fr': 'Les Peintres Carache' # Traduzione placeholder FR (Regolare se necessario)
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

        # Inserimento POI
        if POI_MARKER in content:
            content = content.replace(POI_MARKER, new_poi_injection)
            print(f"✅ Inserito POI in main.js")
        else:
            print(f"⚠️ ATTENZIONE: Marcatore POI non trovato: '{POI_MARKER}'")

        # Inserimento NAV LINK DATA
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
                new_block['audioSource'] = f"{lang}/{page_id}.mp3"
                
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
    match = re.search(r'-([a-z]{2})\.html$', filename)
    if match:
        return match.group(1)
    
    # La pagina base (es. index.html) è trattata a parte o è l'italiano di default
    if filename.endswith('.html') and filename != HTML_TEMPLATE_NAME:
        return 'it_default' 
    return None

def generate_language_switcher(page_id, current_lang):
    """Genera i tag <li> per il cambio lingua."""
    switcher_html = ['<ul class="language-switcher">']
    
    for lang in LANGUAGES:
        # Crea il nome del file specifico per la lingua (es. pittoricarracci-en.html)
        target_file = f'{page_id}-{lang}.html'
        
        # Determina la classe per il link attivo
        is_active = ' active' if lang == current_lang else ''
        
        # Link structure: <a href="pittoricarracci-en.html" lang="en">English</a>
        switcher_html.append(
            f'        <li class="lang-item{is_active}"><a href="{target_file}" lang="{lang}">{LANGUAGE_NAMES[lang]}</a></li>'
        )
        
    switcher_html.append('    </ul>')
    return '\n'.join(switcher_html)

def update_html_files(repo_root, page_id, nav_key_id, translations, page_title_it):
    """
    1. Crea i 4 nuovi file HTML con suffisso lingua e inietta il navigatore linguistico.
    2. Crea il file base di reindirizzamento ({page_id}.html).
    3. Aggiorna TUTTI i file HTML esistenti (navigazione principale e cache).
    """
    
    MARKER_MAIN_NAV = HTML_NAV_MARKER # Il tag </ul> per il menu principale
    MARKER_LANG_SWITCHER = LANGUAGE_SWITCHER_MARKER # Marcatore per il cambio lingua
    
    today_version = datetime.datetime.now().strftime("%Y%m%d_%H%M") 
    template_path = os.path.join(repo_root, HTML_TEMPLATE_NAME)

    # ----------------------------------------------
    # 1. CREAZIONE NUOVE PAGINE SPECIFICHE PER LINGUA
    # ----------------------------------------------
    if not os.path.exists(template_path):
        print(f"ERRORE FATALE: Template HTML non trovato: {HTML_TEMPLATE_NAME}. Impossibile creare le pagine.")
        return

    for lang in LANGUAGES:
        new_page_filename = f'{page_id}-{lang}.html'
        new_page_path = os.path.join(repo_root, new_page_filename)

        if not os.path.exists(new_page_path):
            # Copia dal template
            shutil.copyfile(template_path, new_page_path)
            
            with open(new_page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1a. Aggiorna l'ID del body e il tag <html> lang
            content = content.replace('id="template"', f'id="{page_id}"')
            content = re.sub(r'<html lang="[a-z]{2}">', f'<html lang="{lang}">', content)
            
            # 1b. INIETTA IL NAVIGATORE LINGUISTICO
            lang_switcher_html = generate_language_switcher(page_id, lang)
            if MARKER_LANG_SWITCHER in content:
                content = content.replace(MARKER_LANG_SWITCHER, lang_switcher_html)
            else:
                print(f"⚠️ ATTENZIONE: Marcatore cambio lingua '{MARKER_LANG_SWITCHER}' non trovato nel template. Saltata iniezione navigatore per {lang}.")

            with open(new_page_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Creato NUOVO FILE LINGUA: {new_page_filename}")
        else:
            print(f"⚠️ Pagina {new_page_filename} esiste già. Saltata creazione.")

    # ----------------------------------------------------
    # 2. CREAZIONE NUOVO FILE BASE DI REINDIRIZZAMENTO
    # ----------------------------------------------------
    new_page_base_filename = f'{page_id}.html'
    new_page_base_path = os.path.join(repo_root, new_page_base_filename)
    
    if not os.path.exists(new_page_base_path):
        shutil.copyfile(template_path, new_page_base_path)
        
        with open(new_page_base_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Aggiorna l'ID del body e imposta la lingua di default (IT)
        content = content.replace('id="template"', f'id="{page_id}"')
        content = re.sub(r'<html lang="[a-z]{2}">', f'<html lang="it">', content)
        
        # Rimuovi il placeholder del navigatore linguistico (non necessario nella pagina base, sarà gestito da JS)
        content = content.replace(MARKER_LANG_SWITCHER, '')
        
        # Sostituisci i riferimenti interni al template-it.html con il file base
        content = content.replace(f'href="template-it.html"', f'href="{page_id}.html"')

        with open(new_page_base_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"✅ Creato NUOVO FILE BASE DI REINDIRIZZAMENTO: {new_page_base_filename}")
        
    # ----------------------------------------------------------------------
    # 3. AGGIORNAMENTO DI TUTTI I FILE HTML ESISTENTI (NAVIGAZIONE E CACHE)
    # ----------------------------------------------------------------------
    
    all_html_files = [
        os.path.join(repo_root, f) 
        for f in os.listdir(repo_root) 
        if f.endswith('.html')
    ]
    
    for existing_path in all_html_files:
        try:
            filename = os.path.basename(existing_path)
            
            # Salta i file che non devono avere un link principale
            if filename == HTML_TEMPLATE_NAME:
                continue 

            with open(existing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Link da iniettare: PUNTA SEMPRE AL FILE BASE ({page_id}.html)
            nav_link_href = f'{page_id}.html'
            
            # Genera il link, usando la chiave di traduzione del menu
            nav_link_to_insert = (
                f'        <li><a id="{nav_key_id}" href="{nav_link_href}">'
                f'{{{{ {nav_key_id} }}}}</a></li>' # Uso la sintassi di Handlebars/Text che il tuo main.js userà per il rendering
            )
            
            injection_string = nav_link_to_insert + '\n    ' + MARKER_MAIN_NAV
            
            # 1. Iniezione del link nel menu: SOSTITUIAMO </ul> con [NUOVO LINK] + </ul>
            if MARKER_MAIN_NAV in content and nav_link_to_insert not in content:
                content = content.replace(MARKER_MAIN_NAV, injection_string)
                print(f"✅ Aggiunto link principale a {filename} (target: {nav_link_href})")
                
            # 2. Aggiornamento Cache Busting
            content = re.sub(r'main\.js\?v=([0-9A-Z_]*)', f'main.js?v={today_version}', content)
            
            with open(existing_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Aggiornata cache in {filename}")

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
    
    print("\n=================================================")
    print(f"AVVIO CREAZIONE PAGINA: {page_id}")
    print("=================================================")

    # 1. Recupero traduzioni per la navigazione
    translations = get_translations_for_nav(page_title_it)

    print("\n--- AGGIORNAMENTO JSON ---")
    update_texts_json_nav(repo_root, page_id, nav_key_id, translations)
    
    print("\n--- AGGIORNAMENTO MAIN.JS ---")
    update_main_js(repo_root, page_id, nav_key_id, lat, lon, distance)

    print("\n--- AGGIORNAMENTO HTML E CREAZIONE NUOVE PAGINE ---")
    # L'aggiornamento HTML ora include la creazione dei file specifici per lingua
    update_html_files(repo_root, page_id, nav_key_id, translations, page_title_it)

if __name__ == "__main__":
    main()