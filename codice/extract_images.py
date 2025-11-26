import sys
import os
import re
from docx import Document
from PIL import Image
from io import BytesIO

# --- CONFIGURAZIONI ---
DOCX_DIR = "DOCS_DA_CONVERTIRE"
ASSETS_BASE_DIR = "Assets/images"

# Pattern per identificare il marker e catturare il nome del file desiderato
# Esempio: [SPLIT_BLOCK: nome_file.jpg]
SPLIT_BLOCK_PATTERN = r'\[SPLIT_BLOCK:\s*(.+?\.(?:jpg|jpeg|png|gif|bmp))\]'

def get_target_filename(paragraph):
    """Estrae il nome del file immagine dal marker [SPLIT_BLOCK]"""
    match = re.search(SPLIT_BLOCK_PATTERN, paragraph.text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def extract_images_from_docx(page_id, docx_filename):
    # 1. Normalizzazione del Page ID
    # Questo è fondamentale per la robustezza: garantisce che la cartella sia sempre in minuscolo
    normalized_page_id = page_id.lower()
    
    docx_path = os.path.join(DOCX_DIR, docx_filename)
    if not os.path.exists(docx_path):
        print(f"ERRORE: File DOCX non trovato: {docx_path}", file=sys.stderr)
        return False, 0, 0

    output_dir = os.path.join(ASSETS_BASE_DIR, normalized_page_id)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Directory di output creata: {output_dir}")

    try:
        document = Document(docx_path)
    except Exception as e:
        print(f"ERRORE: Impossibile aprire il documento DOCX '{docx_path}': {e}", file=sys.stderr)
        return False, 0, 0

    doc_images = []
    markers_found = 0

    # 2. Scansione dei paragrafi per trovare i marker [SPLIT_BLOCK]
    for paragraph in document.paragraphs:
        target_filename = get_target_filename(paragraph)
        if target_filename:
            doc_images.append(target_filename)
            markers_found += 1

    print(f"Numero di immagini trovate nel DOCX: {len(doc_images)}")
    print(f"Numero di marker [SPLIT_BLOCK: ...] trovati: {markers_found}")

    extracted_count = 0

    # 3. Estrazione dei dati immagine (blb) dal DOCX
    for rel_id, rel in document.part.rels.items():
        if "image" in rel.target_ref:
            try:
                # *** CORREZIONE DEL BUG: SINTASSI MODERNA PER RECUPERARE IL BLOB ***
                image_part = rel.target_part
                image_bytes = image_part.blob

                # 4. Associa l'immagine al nome desiderato
                if extracted_count < len(doc_images):
                    target_filename = doc_images[extracted_count]
                    output_path = os.path.join(output_dir, target_filename)

                    # Utilizza Pillow per aprire e salvare come JPG (o mantenere il formato specificato)
                    with Image.open(BytesIO(image_bytes)) as img:
                        # Assicurati che l'estensione nel marker corrisponda al formato di salvataggio (se necessario)
                        # Qui salviamo come JPG per semplificare, ma Pillow gestisce l'estensione nel nome.
                        img.save(output_path, format=img.format if not target_filename.lower().endswith('.jpg') else 'jpeg')
                    
                    print(f"✅ Immagine estratta e salvata (formato originale/JPG): {output_path}")
                    extracted_count += 1
                
            except Exception as e:
                # Logga l'errore specifico, ma continua
                print(f"ERRORE durante l'estrazione di un'immagine: {e}", file=sys.stderr)
                # Incrementa extracted_count solo se il marker è stato consumato, ma qui non lo facciamo
                # per mantenere la sincronizzazione con i marker trovati. Continuiamo solo.
                continue 

    print(f"\nEstrazione immagini completata. Estratte {extracted_count} immagini.")
    return True, markers_found, extracted_count

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python extract_images.py [ID_pagina] [nome_file_docx]", file=sys.stderr)
        sys.exit(1)
        
    PAGE_ID = sys.argv[1]
    DOCX_FILE = sys.argv[2]
    
    success, markers, extracted = extract_images_from_docx(PAGE_ID, DOCX_FILE)
    
    if success and markers == extracted:
        sys.exit(0)
    elif success and markers != extracted:
        print(f"ATTENZIONE: Trovati {markers} marker ma estratte {extracted} immagini.", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(1)