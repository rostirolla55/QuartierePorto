import sys
import os
import re
from docx import Document
from docx.table import Table

# --- CONFIGURAZIONI ---
DOCX_DIR = "DOCS_DA_CONVERTIRE"
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
    
    # Se l'elemento è una tabella, gestiamo solo le celle di testo semplici
    if isinstance(element, Table):
        # Ignoriamo le tabelle complesse per ora, gestiamo solo paragrafi
        return html_content 
        
    # --- Gestione dei Paragrafi ---
    
    # 1. Estrai il testo e converti la formattazione di base (grassetto/corsivo)
    
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
        img_src = f"{ASSETS_BASE_DIR}/{page_id}/{image_filename}"
        
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
    Converte l'intero documento e lo divide in due file HTML
    al primo marker [SPLIT_BLOCK].
    """
    docx_path = os.path.join(DOCX_DIR, docx_filename)
    
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

    html_block_1 = []
    html_block_2 = []
    
    # Iniziamo nel primo blocco
    current_block = html_block_1 
    split_found = False

    # Iterazione sugli elementi del documento (paragrafi e tabelle)
    for element in document.element.body.iter():
        
        if element.tag.endswith('p'):  # Paragrafo
            paragraph = document.paragraphs[element.getparent().index(element)]
            
            # 1. Controlla se il paragrafo contiene il marker (punto di split)
            marker_match = re.search(SPLIT_BLOCK_PATTERN, paragraph.text, re.IGNORECASE)
            
            if marker_match and not split_found:
                # Trovato il punto di split!
                split_found = True
                
                # Converti il paragrafo stesso in HTML (contiene l'immagine)
                html_content = docx_to_html(paragraph, page_id)
                current_block.append(html_content)
                
                # Passa al secondo blocco.
                current_block = html_block_2
                print(f"Punto di split trovato e attivato. Prossimo contenuto in {page_id}_2.html.")
                continue # Vai al prossimo elemento del DOCX

            # 2. Converti l'elemento e aggiungi al blocco corrente
            html_content = docx_to_html(paragraph, page_id)
            current_block.append(html_content)
        
        # Aggiungere qui la logica per le tabelle (element.tag.endswith('tbl')) se necessario
        
    # --- Salvataggio dei File ---
    
    base_filename = os.path.splitext(docx_filename)[0]
    
    # 1. Salvataggio del BLOCCO 1
    html_1_filename = f"{base_filename}_1.html"
    html_1_path = os.path.join(HTML_OUTPUT_DIR, html_1_filename)
    
    with open(html_1_path, 'w', encoding='utf-8') as f:
        # Unisce le parti HTML del blocco 1
        f.write("\n".join(html_block_1))
        
    print(f"\n✅ Blocco HTML 1 salvato: {html_1_path}")

    # 2. Salvataggio del BLOCCO 2
    html_2_filename = f"{base_filename}_2.html"
    html_2_path = os.path.join(HTML_OUTPUT_DIR, html_2_filename)
    
    with open(html_2_path, 'w', encoding='utf-8') as f:
        # Unisce le parti HTML del blocco 2
        f.write("\n".join(html_block_2))
        
    print(f"✅ Blocco HTML 2 salvato: {html_2_path}")
    
    return True

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