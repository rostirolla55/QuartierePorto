import os
import re
from typing import List

# Configurazione (deve corrispondere alla cartella di input del key_synchronization_v2.py)
FRAGMENTS_DIR = "text_files"

def clean_html_fragment(html_content: str) -> str:
    """
    Pulisce il contenuto HTML rimuovendo intestazioni complete (DOCTYPE, head, body)
    e incapsulando il corpo rimanente in un div contenitore.
    """
    
    # 1. Rimuovi DOCTYPE e blocchi HEAD
    # Questo cerca e rimuove tutto dall'inizio fino al primo tag <body>
    body_match = re.search(r'<body[^>]*>(.*)', html_content, re.DOTALL | re.IGNORECASE)
    
    if body_match:
        # Trovato il corpo, prendiamo il contenuto dopo <body>
        clean_content = body_match.group(1).strip()
    else:
        # Nessun <body> trovato, prendiamo tutto il contenuto e lo puliamo solo dei tag noti
        clean_content = html_content.strip()

    # 2. Rimuovi i tag </body> e </html> rimanenti alla fine
    clean_content = re.sub(r'</body[^>]*>\s*</html>\s*$', '', clean_content, flags=re.IGNORECASE | re.DOTALL).strip()
    
    # 3. Aggiungi il contenitore radice per l'iniezione
    final_fragment = f'<div class="main-text-content">\n{clean_content}\n</div>'
    
    return final_fragment

def process_fragments(directory: str):
    """
    Scorre la directory e pulisce tutti i file HTML che potrebbero essere frammenti.
    """
    print(f"Inizio pulizia dei frammenti HTML nella directory: {directory}")
    processed_count = 0
    
    # Assumiamo che tutti i file .html in questa directory siano frammenti da pulire
    html_files = [f for f in os.listdir(directory) if f.endswith(".html")]
    
    if not html_files:
        print("Nessun file HTML trovato da pulire.")
        return

    for filename in html_files:
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            cleaned_content = clean_html_fragment(original_content)
            
            # Scrivi il contenuto pulito sullo stesso file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            
            print(f"  - Pulito e aggiornato: {filename}")
            processed_count += 1
            
        except Exception as e:
            print(f"  - ERRORE durante la pulizia di {filename}: {e}")

    print(f"✅ Pulizia completata. {processed_count} file processati.")

if __name__ == "__main__":
    process_fragments(FRAGMENTS_DIR)