import sys
import re
import html
import os

def sanitize_html_to_text(html_content):
    # 1. Decodifica le entity HTML (es. &egrave; -> è)
    content = html.unescape(html_content)

    # 2. Rimuovi tutti i tag HTML, lasciando solo il testo
    # Sostituiamo i tag di blocco con un newline per separazione
    content = re.sub(r'</p>', '\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<[^>]*>', '', content)

    # 3. Pulisci spazi bianchi multipli e a capo
    content = re.sub(r'[ \t]{2,}', ' ', content) # Sostituisce spazi orizzontali multipli con uno spazio singolo
    content = re.sub(r'\n{3,}', '\n\n', content).strip() # Sostituisce a capo multipli con al massimo due
    
    # 4. JSON Escape (necessario per inserimento diretto nel JSON)
    content = content.replace('\\', '\\\\')
    content = content.replace('"', '\\"')
    content = content.replace('\n', '\\n')

    return content

# Assicurati che l'input sia fornito
if len(sys.argv) < 3:
    # Aggiornato per richiedere input_filename e output_filename
    print("ERRORE: Devi passare il nome del file HTML da sanificare e il nome del file TXT di output.", file=sys.stderr)
    sys.exit(1)

input_filename = sys.argv[1]
output_filename = sys.argv[2] # Riceve il nome del file .txt come argomento

try:
    # Apri il file HTML di input
    with open(input_filename, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Sanificazione
    sanitized_text = sanitize_html_to_text(html_content)

    # Scrivi il testo sanificato nel file di output
    # NOTA: In caso di successo, NON stampiamo nulla su sys.stdout
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(sanitized_text)
    
    # Uscita 0 (Successo)
    sys.exit(0)

except FileNotFoundError:
    # ERRORE: Scrive su stderr
    print(f"ERRORE: File di input non trovato: {input_filename}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    # ERRORE: Scrive su stderr
    print(f"ERRORE durante l'elaborazione del file: {e}", file=sys.stderr)
    sys.exit(1)