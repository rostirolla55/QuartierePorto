import sys
import os
from docx import Document
import re
from PIL import Image
import io

# --- CONFIGURAZIONI ---
DOCX_DIR = "DOCS_DA_CONVERTIRE"
OUTPUT_BASE_DIR = "Assets/images"

# Pattern CORRETTO per il marker: cerca [SPLIT_BLOCK: filename.ext]
# Non c'è uno spazio tra il punto e l'estensione.
SPLIT_BLOCK_PATTERN = r'\[SPLIT_BLOCK:\s*(.+?\.(?:jpg|jpeg|png|gif|bmp))\]'

def extract_and_rename_images(page_id, docx_filename):
    """
    Estrae le immagini da un documento DOCX e le rinomina in base ai marker [SPLIT_BLOCK:...].
    Le immagini vengono estratte in ordine e associate ai marker trovati in ordine.
    """
    
    docx_path = os.path.join(DOCX_DIR, docx_filename)
    output_page_dir = os.path.join(OUTPUT_BASE_DIR, page_id)

    if not os.path.exists(docx_path):
        print(f"ERRORE: File DOCX non trovato: {docx_path}", file=sys.stderr)
        return False
    
    # Crea la directory di output
    os.makedirs(output_page_dir, exist_ok=True)
    print(f"Directory di output creata: {output_page_dir}")

    try:
        document = Document(docx_path)
    except Exception as e:
        print(f"ERRORE: Impossibile aprire il documento DOCX '{docx_path}': {e}", file=sys.stderr)
        return False

    extracted_count = 0
    
    # 1. Lista dei nomi di file dai marker nel documento (in ordine)
    found_marker_names = []
    for paragraph in document.paragraphs:
        # Cerchiamo il marker con il pattern corretto
        marker_match = re.search(SPLIT_BLOCK_PATTERN, paragraph.text, re.IGNORECASE)
        if marker_match:
            found_marker_names.append(marker_match.group(1).strip())
            
    # 2. Lista delle immagini estratte con i loro bytes originali (in ordine)
    all_extracted_media = []
    
    # Iteriamo su tutte le 'relationships' (inclusi media) per trovare le immagini
    for rId, part in document.part.related_parts.items():
        if part.partname.startswith('/word/media/'):
            all_extracted_media.append(part.blob)

    print(f"Numero di immagini trovate nel DOCX: {len(all_extracted_media)}")
    print(f"Numero di marker [SPLIT_BLOCK: ...] trovati: {len(found_marker_names)}")
        
    # 3. Associa le immagini ai nomi dei marker e salvale
    if len(all_extracted_media) != len(found_marker_names):
        print("!!! AVVISO DI DISCREPANZA !!!", file=sys.stderr)
        print(f"Il numero di immagini ({len(all_extracted_media)}) NON corrisponde al numero di marker ({len(found_marker_names)}).", file=sys.stderr)
        print("L'estrazione non sarà precisa. Controlla il file DOCX e i marker.", file=sys.stderr)
        
    
    # Processiamo solo il minimo tra immagini e marker per evitare errori di indice
    limit = min(len(all_extracted_media), len(found_marker_names))

    for idx in range(limit):
        image_bytes = all_extracted_media[idx]
        target_image_name = found_marker_names[idx]
        output_filename = os.path.join(output_page_dir, target_image_name)

        try:
            # Tentativo di salvare/convertire l'immagine
            # Se il nome del target è JPG/JPEG, forziamo la conversione in JPG
            if target_image_name.lower().endswith(('.jpg', '.jpeg')):
                img = Image.open(io.BytesIO(image_bytes))
                
                # Assicuriamo che sia RGB prima di salvare in JPG
                if img.mode in ('RGBA', 'P'):
                    img = img.convert("RGB")
                    
                img.save(output_filename)
                print(f"✅ Immagine estratta e salvata (convertita in JPG): {output_filename}")
            else:
                # Altrimenti, salviamo i bytes originali con l'estensione del marker
                with open(output_filename, 'wb') as img_file:
                    img_file.write(image_bytes)
                print(f"✅ Immagine estratta e salvata: {output_filename}")
                
            extracted_count += 1
        except Exception as img_e:
            print(f"❌ ERRORE salvataggio immagine {target_image_name}: {img_e}", file=sys.stderr)
            
    print(f"\nEstrazione immagini completata. Estratte {extracted_count} immagini.")
    return extracted_count > 0

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python extract_images.py [ID_pagina] [nome_file_docx]", file=sys.stderr)
        print("Esempio: python extract_images.py pittoricarracci it_pittoricarracci_maintext.docx", file=sys.stderr)
        sys.exit(1)
        
    PAGE_ID = sys.argv[1]
    DOCX_FILE = sys.argv[2]
    
    if extract_and_rename_images(PAGE_ID, DOCX_FILE):
        sys.exit(0)
    else:
        sys.exit(1)