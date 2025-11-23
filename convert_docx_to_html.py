import sys
import os
import re
from docx import Document
from docx.table import Table

# --- CONFIGURAZIONI ---
DOCS_DIR = "DOCS_DA_CONVERTIRE"
HTML_OUTPUT_DIR = "HTML_OUTPUT"
ASSETS_BASE_DIR = "Assets/images"

# Pattern per il marker. Usa lo stesso pattern del file di estrazione immagini.
SPLIT_BLOCK_PATTERN = r'\[SPLIT_BLOCK:\s*(.+?\.(?:jpg|jpeg|png|gif|bmp))\]'

def docx_to_html(element, page_id):
    """
    Converte un elemento (paragrafo o cella di tabella) in HTML,
    sostituendo i marker immagine con tag <img>.
    """
    html_content = ""
    
    # Ignora le tabelle complesse per ora
    if isinstance(element, Table):
        return html_content 
        
    # --- Gestione dei Paragrafi ---
    
    text_buffer = []
    
    # Costruisce il testo, mantenendo i tag di formattazione inline
    for run in element.runs:
        current_text = run.text
        
        # Gestione del grassetto e del corsivo
        if run.bold:
            current_text = f"<strong>{current_text}</strong>"
        if run.italic:
            current_text = f"<em>{current_text}</em>"
            
        text_buffer.append(current_text)

    raw_text = "".join(text_buffer)
    
    # 2. Sostituzione del Marker Immagine con Tag <img>
    
    def replace_marker(match):
        """Sostituisce il marker con il tag <img> corretto."""
        image_filename = match.group(1).strip()
        
        # Percorso dell'immagine: Assets/images/page_id/nomefile.jpg
        # NOTA: Usiamo normalized_page_id che è già in minuscolo
        img_src = f"{ASSETS_BASE_DIR}/{page_id.lower()}/{image_filename}"
        
        # Restituisce il tag <img> per l'HTML
        return f'<img src="{img_src}" alt="{image_filename}">'

    # Applica la sostituzione
    html_with_images = re.sub(SPLIT_BLOCK_PATTERN, replace_marker, raw_text, flags=re.IGNORECASE)
    
    # 3. Wrapping del Paragrafo con <p>
    if html_with_images.strip():
        # Aggiungi qui eventuali classi HTML se necessario
        html_content = f"<p>{html_with_images.strip()}</p>"

    return html_content

def convert_docx_and_split(page_id, docx_filename):
    """
    Converte l'intero documento e lo divide in più file HTML
    ad ogni marker [SPLIT_BLOCK] trovato (logica dinamica).
    """
    # 1. Normalizzazione del Page ID prima di usarlo
    normalized_page_id = page_id.lower()
    
    docx_path = os.path.join(DOCS_DIR, docx_filename)
    
    if not os.path.exists(docx_path):
        print(f"ERRORE: File DOCX non trovato: {docx_path}", file=sys.stderr)
        return False

    os.makedirs(HTML_OUTPUT_DIR, exist_ok=True)
    print(f"Directory di output HTML creata: {HTML_OUTPUT_DIR}")
    
    try:
        document = Document(docx_path)
    except Exception as e:
        print(f"ERRORE: Impossibile aprire il documento DOCX '{docx_path}': {e}", file=sys.stderr)
        return False

    # Inizializziamo con una lista di liste. La prima lista è il primo blocco HTML.
    html_blocks = [[]] 
    current_block_index = 0

    # Iterazione sugli elementi del documento (paragrafi e tabelle)
    for element in document.element.body.iter():
        
        if element.tag.endswith('p'):  # Paragrafo
            paragraph = document.paragraphs[element.getparent().index(element)]
            
            # Controlla se il paragrafo contiene il marker
            marker_match = re.search(SPLIT_BLOCK_PATTERN, paragraph.text, re.IGNORECASE)
            
            if marker_match:
                # 1. Converti il paragrafo contenente il marker e aggiungilo al blocco corrente.
                # In questo modo, il tag <img> viene inserito nel blocco di testo che lo precede.
                html_content = docx_to_html(paragraph, normalized_page_id)
                html_blocks[current_block_index].append(html_content)
                
                # 2. Aumenta l'indice e crea un nuovo blocco di testo.
                current_block_index += 1
                html_blocks.append([]) 
                
                print(f"Punto di split trovato (Marker {current_block_index}). Prossimo contenuto in _{current_block_index + 1}.html.")
                continue # Passa al prossimo elemento del DOCX

            # Se non è un marker, aggiungi il contenuto al blocco corrente
            html_content = docx_to_html(paragraph, normalized_page_id)
            if html_content:
                html_blocks[current_block_index].append(html_content)
        
    # --- Salvataggio dei File ---
    
    base_filename = os.path.splitext(docx_filename)[0]
    
    # Rimuovi l'ultimo blocco se è vuoto (succede se il DOCX finisce con un marker)
    if html_blocks and not html_blocks[-1] and len(html_blocks) > 1:
        html_blocks.pop()

    num_blocks = len(html_blocks)
    print(f"\n--- Salvataggio di {num_blocks} blocchi HTML ---")

    for i, block in enumerate(html_blocks):
        # I file iniziano da _1.html
        block_number = i + 1 
        html_filename = f"{base_filename}_{block_number}.html"
        html_path = os.path.join(HTML_OUTPUT_DIR, html_filename)
        
        # Salva solo se il blocco contiene contenuto
        if block: 
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(block))
                
            print(f"✅ Blocco HTML {block_number} salvato: {html_path}")
        else:
            print(f"⚠️ Blocco HTML {block_number} vuoto. File non generato.")


    return num_blocks > 0

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python convert_docx_to_html.py [ID_pagina] [nome_file_docx]", file=sys.stderr)
        sys.exit(1)
        
    PAGE_ID = sys.argv[1]
    DOCX_FILE = sys.argv[2]
    
    if convert_docx_and_split(PAGE_ID, DOCX_FILE):
        sys.exit(0)
    else:
        sys.exit(1)