import sys
import os
import re

# Directory dove si trova l'HTML generato dal tuo tool DOCX-to-HTML
INPUT_HTML_DIR = "text_files" 
# Directory dove salvare l'HTML splittato
OUTPUT_HTML_DIR = "text_files" 
# Pattern per il marker: cattura tutto il marker e il nome del file immagine
SPLIT_PATTERN = r'(\[SPLIT_BLOCK:\s*(.+?)\])' 

def process_html_for_page(lang_code, page_id):
    """
    Legge l'HTML intero, splitta i blocchi e genera le righe JSON.
    """
    
    # Costruisci il nome del file HTML di input
    input_filename = f"{lang_code}_{page_id}_maintext.html"
    input_path = os.path.join(INPUT_HTML_DIR, input_filename)
    
    if not os.path.exists(input_path):
        print(f"ERRORE: File HTML di input non trovato: {input_path}", file=sys.stderr)
        print("Assicurati che la conversione DOCX-to-HTML sia stata eseguita e che il file sia in text_files/.", file=sys.stderr)
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        full_html_string = f.read()

    # 1. Splitting avanzato: Mantiene il marker per l'estrazione del nome immagine
    # 'parts' conterrà: [Blocco 1 HTML, Marker 1, Nome Immagine 1, Blocco 2 HTML, Marker 2, Nome Immagine 2, ...]
    parts = re.split(SPLIT_PATTERN, full_html_string)
    
    html_blocks = []
    
    # Rimuoviamo il primo elemento 'Marker' (group 1) e teniamo solo il nome del file (group 2)
    # Re.split con due gruppi di cattura non funziona in modo pulito come vorremmo qui,
    # quindi ricarichiamo i blocchi e le sorgenti dall'array 'parts' filtrato.
    
    # Ricostruzione: le posizioni 0, 3, 6, etc. sono i blocchi HTML
    # Le posizioni 2, 5, 8, etc. contengono il nome del file immagine
    
    # Il primo elemento è sempre il Blocco 1 HTML
    if parts:
        html_blocks.append(parts[0].strip()) 
        
    image_sources = []
    
    # Iteriamo sui marker e i nomi delle immagini
    # Partiamo da i=1 (dove c'è il primo [SPLIT_BLOCK: ...])
    for i in range(1, len(parts), 3):
        
        # Aggiungiamo il blocco HTML successivo
        if i + 2 < len(parts):
             # parts[i+2] è il blocco HTML (Blocco 2, Blocco 3, ecc.)
             html_blocks.append(parts[i+2].strip())
        
        # Estraiamo il nome dell'immagine (parts[i+1] è il nome del file)
        # Il pattern SPLIT_PATTERN sopra definito cattura:
        # group 1: '[SPLIT_BLOCK: nome_immagine.jpg]'
        # group 2: 'nome_immagine.jpg'
        # quindi parts avrà [HTML1, [SPLIT_BLOCK: nome], nome, HTML2, [SPLIT_BLOCK: nome], nome, ...]
        
        # Poiché re.split con gruppi di cattura è imprevedibile, usiamo un metodo più sicuro:
        # Splittiamo solo sul marker e poi estraiamo il nome dal marker stesso.
        
    # --- METODO PIÙ ROBUSTO PER LO SPLITTING ---
    
    # Semplifichiamo lo split (rimuovendo il secondo gruppo di cattura nel pattern)
    SPLIT_PATTERN_SIMPLE = r'(\[SPLIT_BLOCK:.*?\])' 
    parts = re.split(SPLIT_PATTERN_SIMPLE, full_html_string)
    
    html_blocks = []
    image_sources = []

    # Iteriamo sulle parti (posizioni pari=HTML, dispari=MARKER)
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # Posizione pari: è un blocco HTML
            html_blocks.append(parts[i].strip())
        else:
            # Posizione dispari: è il marker [SPLIT_BLOCK: nome.ext]
            marker = parts[i]
            match = re.search(r':\s*(.+?)\]', marker)
            if match:
                image_sources.append(match.group(1).strip())
            else:
                image_sources.append("") 
                
    # --- FINE METODO ROBUSTO ---


    # 2. Salvataggio Blocchi e Generazione JSON
    json_lines = []
    os.makedirs(OUTPUT_HTML_DIR, exist_ok=True) 

    print("\n==========================================================")
    print(f"Generazione Output per la pagina: {page_id}")
    print("==========================================================")

    for i, block_html in enumerate(html_blocks):
        block_index = i + 1
        
        if not block_html:
            continue # Salta blocchi HTML vuoti che potrebbero derivare dallo splitting

        # A. Salvataggio del Blocco HTML (maintext1.html, maintext2.html...)
        output_filename = f"{lang_code}_{page_id}_maintext{block_index}.html"
        output_path = os.path.join(OUTPUT_HTML_DIR, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(block_html)
            
        # Generazione della riga JSON per il testo (Corretto: NO prefisso lingua)
        json_line_text = f'"mainText{block_index}": "{output_filename}"'
        json_lines.append(json_line_text)
        
        # B. Aggiunta dell'ImageSource: l'immagine N è associata al Blocco HTML N+1
        # L'immagine al l'indice i nell'array image_sources è quella che precede il Blocco HTML i+1
        if i < len(image_sources):
            img_name = image_sources[i] 
            
            if img_name:
                # CREAZIONE DEL PERCORSO COMPLETO (ID_PAGINA/NOME_IMMAGINE.EXT)
                image_path_in_json = f"{page_id}/{img_name}" 
                
                # La chiave JSON usa un indice separato da quello del mainText
                json_line_img = f'"imageSource{block_index}": "{image_path_in_json}"'
                json_lines.append(json_line_img)
            
        
    print("File HTML splittati e salvati in text_files/.")
    print("\n*** RIGHE JSON GENERATE (Copia e Incolla nel tuo file JSON) ***")
    for line in json_lines:
        print(line + ",")
    print("*************************************************************")

    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python process_html_and_json.py [codice_lingua] [ID_pagina]", file=sys.stderr)
        sys.exit(1)
        
    LANG_CODE = sys.argv[1].lower()
    PAGE_ID = sys.argv[2].lower()
    
    if process_html_for_page(LANG_CODE, PAGE_ID):
        sys.exit(0)
    else:
        sys.exit(1)