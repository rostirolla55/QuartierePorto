import sys
import re
import html
import os

def sanitize_html_to_text(html_content):
    """
    Rimuove i tag HTML in modo robusto, pulisce gli spazi e mantiene i caratteri di newline (\n)
    come separatori di riga leggibili, senza escape letterale.
    """
    
    # Placeholder temporaneo per proteggere i newline generati dalla sostituzione dei tag
    NEWLINE_PLACEHOLDER = "@@@NEWLINE@@@"
    
    # 1. Decodifica le entity HTML (es. &egrave; -> è)
    content = html.unescape(html_content)

    # 2. Rimuovi tutti i tag HTML e inserisci il placeholder per i paragrafi
    # Sostituiamo i tag di blocco con il placeholder
    content = re.sub(r'</p>', NEWLINE_PLACEHOLDER, content)
    content = re.sub(r'<br\s*/?>', NEWLINE_PLACEHOLDER, content)
    
    # Rimuoviamo il resto dei tag HTML (inclusi <img>, <strong>, ecc.)
    content = re.sub(r'<[^>]*>', '', content)
    
    # 3. Pulizia sequenze di newline non volute e artefatti di escape.
    
    # 3a. Rimuove la sequenza letterale di newline e virgolette lasciate dal fallimento del tag <img>:
    # Pattern robusto per eliminare residui di tag immagine (es. nomefile.jpg\" alt=\"nomefile.jpg\">;)
    content = re.sub(r'\s*([a-zA-Z0-9_-]+\.(?:jpg|jpeg|png|gif|bmp))\\?"\s*alt=\\?"\1\\?"\s*[^;]*;?', '', content, flags=re.IGNORECASE)

    # 3b. Rimuove eventuali sequenze \n letterali che sono rimaste all'inizio delle righe o altrove:
    # Sostituiamo la sequenza di caratteri literal \n con il placeholder
    content = content.replace('\\n', NEWLINE_PLACEHOLDER)
    
    # 4. JSON Escape (solo virgolette e barre rovesciate non-newline)
    # Eseguiamo l'escape delle barre rovesciate (NON parte di un \n) e delle virgolette ORA.
    # Questo è il punto critico per evitare che \n diventi \\n.
    
    # Escape delle barre rovesciate: sostituisce \ con \\
    content = content.replace('\\', '\\\\')
    # Escape delle virgolette: sostituisce " con \"
    content = content.replace('"', '\\"')

    # 5. Pulizia spazi bianchi e conversione placeholder
    
    # 5a. Sostituisce il placeholder con il vero carattere di newline (\n)
    # Poiché l'escape delle barre rovesciate è avvenuto prima, questo \n non verrà mai trasformato in \\n.
    content = content.replace(NEWLINE_PLACEHOLDER, '\n')
    
    # 5b. Pulisci spazi orizzontali multipli
    content = re.sub(r'[ \t]{2,}', ' ', content)
    
    # 5c. Pulisci a capo multipli (massimo due per separare i paragrafi) e rimuovi spazi iniziali/finali
    content = re.sub(r'\n{3,}', '\n\n', content).strip()
    
    return content

# Assicurati che l'input sia fornito
if len(sys.argv) < 3:
    # L'output di errore va su stderr
    print("ERRORE: Devi passare il nome del file HTML da sanificare e il nome del file TXT di output.", file=sys.stderr)
    sys.exit(1)

input_filename = sys.argv[1]
output_filename = sys.argv[2] 

try:
    # Apri il file HTML di input
    with open(input_filename, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Sanificazione
    sanitized_text = sanitize_html_to_text(html_content)

    # Scrivi il testo sanificato nel file di output
    # L'output contiene i veri caratteri \n non escapati come sequenze letterali.
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(sanitized_text)
    
    # Uscita 0 (Successo)
    sys.exit(0)

except FileNotFoundError:
    print(f"ERRORE: File di input non trovato: {input_filename}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"ERRORE durante l'elaborazione del file: {e}", file=sys.stderr)
    sys.exit(1)