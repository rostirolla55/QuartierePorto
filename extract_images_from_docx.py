import sys
import os
import re
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# Directory di output per le immagini (modifica se necessario)
IMAGE_OUTPUT_DIR = "assets/images" 
# Pattern per il marker nel testo: [SPLIT_BLOCK: nome_immagine.ext]
MARKER_PATTERN = r'\[SPLIT_BLOCK:\s*(.+?)\]'

def extract_images_and_save(lang_code, page_id):
    """
    Estrae le immagini dal file DOCX e le salva in una sottodirectory specifica.
    """
    
    # Costruisci il percorso del file DOCX (basato sulla convenzione it_arcoxy_maintext.docx)
    input_filename = f"{lang_code}_{page_id}_maintext.docx"
    
    if not os.path.exists(input_filename):
        print(f"ERRORE: File DOCX non trovato: {input_filename}", file=sys.stderr)
        return False

    # Creazione della sottocartella per la pagina, se non esiste
    output_path = os.path.join(IMAGE_OUTPUT_DIR, page_id)
    os.makedirs(output_path, exist_ok=True)
    
    print(f"Tentativo di estrazione immagini da: {input_filename}...")
    
    try:
        document = Document(input_filename)
        media_count = 0
        
        # Iterazione su tutte le relazioni del pacchetto (incluse le immagini)
        for rel in document.part.rels.values():
            if rel.reltype == RT.IMAGE:
                # 1. Estrai i dati binari dell'immagine
                image_part = rel.target_part
                image_bytes = image_part.blob
                
                # 2. Cerca il nome dell'immagine nel testo (dal marker)
                #    NOTA: In docx le immagini sono elementi separati, ma in questo script
                #    assumiamo che il nome sia specificato nel testo *vicino* all'immagine.
                
                # Questa parte è complessa, perché python-docx non associa facilmente 
                # la relazione RT.IMAGE al testo del marker.
                # Per semplificare e rispettare il tuo workflow, chiediamo all'utente di 
                # **rinominare** i file estratti.
                
                # Metodo semplificato: salva l'immagine con il suo nome interno
                # La maggior parte delle immagini ha un nome interno come 'imageX.png'
                
                original_filename = os.path.basename(image_part.partname)
                final_save_path = os.path.join(output_path, original_filename)
                
                with open(final_save_path, "wb") as f:
                    f.write(image_bytes)
                
                print(f"  - Immagine estratta e salvata come: {final_save_path}")
                media_count += 1

        if media_count == 0:
            print("ATTENZIONE: Nessuna immagine trovata nel documento.")
        
        print(f"Estrazione completata. Trovate {media_count} immagini.")

        # ---- IMPORTANTE: ISTRUZIONI PER L'UTENTE SUL RAPPORTO NOME-MARKER ----
        print("\n\n*** OPERAZIONE MANUALE NECESSARIA ***")
        print("Lo script ha salvato le immagini con nomi interni ('image1.png', etc.).")
        print(f"Devi rinominare questi file nella cartella {output_path}")
        print("per farli corrispondere esattamente ai nomi che hai inserito nei marker [SPLIT_BLOCK:...].")
        print("Esempio: 'image1.png' -> 'ingresso_porto.png'")
        print("************************************")
        
        return True
        
    except Exception as e:
        print(f"ERRORE critico durante l'estrazione: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python extract_images_from_docx.py [codice_lingua] [ID_pagina]", file=sys.stderr)
        sys.exit(1)
        
    LANG_CODE = sys.argv[1].lower()
    PAGE_ID = sys.argv[2].lower()
    
    if extract_images_and_save(LANG_CODE, PAGE_ID):
        sys.exit(0)
    else:
        sys.exit(1)