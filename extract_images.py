import sys
import os
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import re
from PIL import Image # Per convertire immagini (es. PNG in JPG se necessario)
import io

# --- CONFIGURAZIONI ---
DOCX_DIR = "DOCS_DA_CONVERTIRE"
OUTPUT_BASE_DIR = "Assets/images"
# Pattern per il marker: cattura il nome del file immagine
SPLIT_BLOCK_PATTERN = r'\[SPLIT_BLOCK:\s*(.+?\. (?:jpg|jpeg|png|gif|bmp))\]' # Modificato per includere estensioni comuni e spazio dopo il punto

def extract_and_rename_images(page_id, docx_filename):
    """
    Estrae le immagini da un documento DOCX e le rinomina in base ai marker [SPLIT_BLOCK:...].
    """
    
    docx_path = os.path.join(DOCX_DIR, docx_filename)
    output_page_dir = os.path.join(OUTPUT_BASE_DIR, page_id)

    if not os.path.exists(docx_path):
        print(f"ERRORE: File DOCX non trovato: {docx_path}", file=sys.stderr)
        return False
    
    os.makedirs(output_page_dir, exist_ok=True)
    print(f"Directory di output creata: {output_page_dir}")

    try:
        document = Document(docx_path)
    except Exception as e:
        print(f"ERRORE: Impossibile aprire il documento DOCX '{docx_path}': {e}", file=sys.stderr)
        return False

    extracted_count = 0
    
    # Per tenere traccia dei marker già utilizzati
    processed_markers = set() 

    # Iteriamo sui paragrafi per trovare immagini e marker associati
    for i, paragraph in enumerate(document.paragraphs):
        text_after_image = paragraph.text.strip()
        
        # Cerchiamo un marker in questo paragrafo
        marker_match = re.search(SPLIT_BLOCK_PATTERN, text_after_image, re.IGNORECASE)

        if marker_match:
            # Abbiamo trovato un marker. Ora cerchiamo l'immagine che lo precede.
            target_image_name = marker_match.group(1).strip()
            
            # Il marker è stato trovato nel testo del paragrafo.
            # Dobbiamo cercare l'immagine nei paragrafi o nelle forme che precedono questo marker.
            # Questo è il punto più complesso: l'immagine e il marker potrebbero non essere nello stesso paragrafo.
            
            # Approccio: scorrere all'indietro dai paragrafi precedenti per trovare un'immagine.
            # In DOCX, le immagini sono spesso "inline" o in "shapes".
            # Questa logica è semplificata e assume che il marker sia vicino all'immagine.

            # Ricerca immagine inline nel paragrafo corrente (prima del marker)
            for j, run in enumerate(paragraph.runs):
                if run.element.xml.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing') is not None:
                    # Trovata immagine inline nel paragrafo!
                    # Ora estraila. Il metodo più affidabile è tramite document.part.related_parts
                    
                    # Cerca l'immagine tra le 'relationships' del documento
                    for rId, part in document.part.related_parts.items():
                        if part.partname.startswith('/word/media/'): # È un file media
                            # Questo è un approccio semplificato per collegare run a rId
                            # Un metodo più robusto richiederebbe l'analisi dell'XML del run
                            # Per ora, proviamo a estrarre la prima immagine media non ancora processata
                            
                            media_name = os.path.basename(part.partname)
                            if media_name not in processed_markers: # Evita di estrarre la stessa immagine
                                image_bytes = part.blob
                                output_filename = os.path.join(output_page_dir, target_image_name)

                                try:
                                    # Prova a salvare l'immagine (puoi aggiungere conversione se necessario)
                                    # Esempio: converti sempre in JPG
                                    if not target_image_name.lower().endswith(('.jpg', '.jpeg')):
                                        print(f"Avviso: {target_image_name} non è JPG. Tentativo di conversione...")
                                        img = Image.open(io.BytesIO(image_bytes))
                                        img = img.convert("RGB") # Assicura RGB per JPG
                                        output_filename_jpg = os.path.splitext(output_filename)[0] + ".jpg"
                                        img.save(output_filename_jpg)
                                        print(f"✅ Immagine salvata come: {output_filename_jpg}")
                                    else:
                                        with open(output_filename, 'wb') as img_file:
                                            img_file.write(image_bytes)
                                        print(f"✅ Immagine salvata come: {output_filename}")
                                    
                                    processed_markers.add(media_name)
                                    extracted_count += 1
                                    break # Passa al prossimo paragrafo
                                except Exception as img_e:
                                    print(f"ERRORE salvataggio immagine {target_image_name}: {img_e}", file=sys.stderr)
                                    
                    if extracted_count > 0: # Se abbiamo già estratto un'immagine, assumiamo che sia per questo marker
                        break 
                
        # Se l'immagine non è inline nel paragrafo del marker, cerchiamo in tutte le relazioni
        # Questo è un metodo più generale ma meno preciso per l'associazione testo-immagine.
        # Un'analisi più fine richiederebbe il parsing dell'XML per capire l'ordine di testo/immagini.
        
        # Iterazione su tutte le 'relationships' (inclusi media)
        for rId, part in document.part.related_parts.items():
            if part.partname.startswith('/word/media/'):
                media_name = os.path.basename(part.partname)
                
                # Se il marker non è stato processato e abbiamo un nome immagine valido
                if marker_match and marker_match.group(1).strip() not in processed_markers:
                    target_image_name = marker_match.group(1).strip()
                    
                    # Verifica se il marker si riferisce all'immagine corrente
                    # Questo è un'euristica: assumiamo che il primo marker trovi la prima immagine, ecc.
                    # Per una precisione maggiore, i marker dovrebbero essere *nell'alt-text* dell'immagine.
                    
                    # Qui la logica diventa complessa per una gestione generica.
                    # Assumiamo che se c'è un marker, la prossima immagine non processata è quella giusta.
                    
                    # Un'alternativa migliore sarebbe leggere il testo circostante all'immagine
                    # e cercare il marker PRIMA di estrarre l'immagine.
                    
                    # Data la complessità dell'associazione run-to-media-name senza parsing XML profondo:
                    # Il metodo più semplice è scorrere le relazioni e, se trovi un marker,
                    # estrai la prossima immagine non estratta e assegnala a quel marker.
                    
                    # Tuttavia, per "rinominare a partire da un marker NEL TESTO", dobbiamo
                    # avere un modo di sapere che QUEL marker è per QUELLA immagine.
                    
                    # Soluzione Pratica 1 (richiede coerenza): Se hai solo una o due immagini e sai l'ordine:
                    # Puoi estrarre le immagini in ordine e assegnare i nomi dai marker in ordine.
                    
                    # Soluzione Pratica 2 (migliore): Inserisci il nome del file desiderato nell'ALT TEXT dell'immagine in Word.
                    # Se il nome è nell'ALT TEXT, lo script python-docx può leggerlo direttamente.
                    
                    # Poiché i tuoi marker sono nel testo, il metodo più diretto è il seguente:
                    # Trova il marker.
                    # Cerca l'immagine più vicina (prima o dopo, a seconda di dove la metti).
                    
                    # Per semplicità, possiamo cercare tutte le immagini, e se troviamo un marker
                    # che non è stato processato, usiamo la prossima immagine disponibile e la rinominiamo.
                    pass # Questa parte è stata spostata in una logica più diretta.

    
    # --- Approccio Alternativo per Associazione: Estrai tutte le immagini e poi rinomina con i marker ---
    # Questo approccio è più robusto se i marker sono nel testo dopo le immagini.
    
    # Lista delle immagini estratte con i loro bytes originali
    all_extracted_media = []
    
    for rId, part in document.part.related_parts.items():
        if part.partname.startswith('/word/media/'):
            all_extracted_media.append(part.blob)

    # Lista dei nomi di file dai marker nel documento
    found_marker_names = []
    for paragraph in document.paragraphs:
        marker_match = re.search(SPLIT_BLOCK_PATTERN, paragraph.text, re.IGNORECASE)
        if marker_match:
            found_marker_names.append(marker_match.group(1).strip())
            
    # Ora, associa le immagini estratte in ordine ai nomi dei marker trovati in ordine
    if len(all_extracted_media) != len(found_marker_names):
        print(f"Avviso: Numero di immagini ({len(all_extracted_media)}) non corrisponde al numero di marker ({len(found_marker_names)}). Potrebbero esserci problemi di rinomina.", file=sys.stderr)

    for idx, image_bytes in enumerate(all_extracted_media):
        if idx < len(found_marker_names):
            target_image_name = found_marker_names[idx]
            output_filename = os.path.join(output_page_dir, target_image_name)

            try:
                # Prova a salvare l'immagine, convertendo in JPG se necessario
                if not target_image_name.lower().endswith(('.jpg', '.jpeg')):
                    img = Image.open(io.BytesIO(image_bytes))
                    img = img.convert("RGB") # Assicura RGB per JPG
                    output_filename_jpg = os.path.splitext(output_filename)[0] + ".jpg"
                    img.save(output_filename_jpg)
                    print(f"✅ Immagine estratta e salvata come: {output_filename_jpg}")
                else:
                    with open(output_filename, 'wb') as img_file:
                        img_file.write(image_bytes)
                    print(f"✅ Immagine estratta e salvata come: {output_filename}")
                extracted_count += 1
            except Exception as img_e:
                print(f"ERRORE salvataggio immagine {target_image_name}: {img_e}", file=sys.stderr)
        else:
            print(f"Avviso: Immagine extra trovata senza un marker corrispondente.", file=sys.stderr)

    print(f"\nEstrazione immagini completata. Estratte {extracted_count} immagini.")
    return True

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