import os
from docx import Document

# --- CONFIGURAZIONE PERCORSI ---
# ADATTA QUESTO: la directory dove si trovano i tuoi 12 file .docx
DOCX_DIR = 'C:/Users/User/Documents/GitHub/QuartierePorto/DOCS_DA_CONVERTIRE' 

# ADATTA QUESTO: la directory di output (dove li vuoi salvare, es. la root del progetto)
HTML_DIR = 'C:/Users/User/Documents/GitHub/QuartierePorto' 
# -------------------------------

def docx_to_html_base():
    """
    Converte tutti i file .docx in DOCX_DIR in file .html in HTML_DIR, 
    usando la formattazione base <p>.
    """
    
    if not os.path.exists(HTML_DIR):
        print(f"La directory di output non esiste: {HTML_DIR}")
        os.makedirs(HTML_DIR)
        
    if not os.path.exists(DOCX_DIR):
        print(f"ERRORE: La directory dei file DOCX sorgente non esiste: {DOCX_DIR}")
        return

    print(f"Avvio conversione da {DOCX_DIR} a {HTML_DIR}...")
    
    for filename in os.listdir(DOCX_DIR):
        if filename.endswith(".docx") and not filename.startswith('~'):
            docx_path = os.path.join(DOCX_DIR, filename)
            
            # Sostituisci l'estensione .docx con .html
            html_filename = filename.replace(".docx", ".html")
            html_path = os.path.join(HTML_DIR, html_filename)
            
            try:
                document = Document(docx_path)
                html_content = ""
                
                for paragraph in document.paragraphs:
                    text = paragraph.text.strip()
                    
                    if text:
                        # Estrae il testo e lo formatta come un paragrafo HTML
                        # Nota: Non gestisce grassetti/liste, da fare a mano se necessario
                        html_content += f"<p>{text}</p>\n"
                
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                print(f"✅ Convertito: {filename} -> {html_filename}")
                
            except Exception as e:
                print(f"ERRORE nella conversione di {filename}: {e}")

if __name__ == "__main__":
    docx_to_html_base()