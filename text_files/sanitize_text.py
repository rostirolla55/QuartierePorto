import sys
import re
import html
import os

def sanitize_html_to_text(html_content):
    """
    Rimuove i tag HTML, pulisce gli spazi e mantiene i caratteri di newline (\n)
    come separatori di riga leggibili, senza escape letterale.
    """
    # 1. Decodifica le entity HTML (es. &egrave; -> è)
    content = html.unescape(html_content)

    # 2. Rimuovi tutti i tag HTML, lasciando solo il testo
    # Sostituiamo i tag di blocco con un newline (\n) per separazione leggibile.
    # Usiamo un placeholder temporaneo per i newline generati.
    NEWLINE_PLACEHOLDER = "@@@NEWLINE@@@"
    
    # Rimuoviamo i tag, inserendo il placeholder di newline.
    content = re.sub(r'</p>', NEWLINE_PLACEHOLDER, content)
    content = re.sub(r'<br\s*/?>', NEWLINE_PLACEHOLDER, content)
    content = re.sub(r'<[^>]*>', '', content)
    
    # Pulizia preliminare: se per qualche motivo il testo conteneva la sequenza \n, la sostituiamo
    content = content.replace('\\n', NEWLINE_PLACEHOLDER)
    
    # 3. JSON Escape di base (solo virgolette e barre rovesciate)
    # Eseguiamo l'escape delle barre rovesciate ORA, prima di convertire i placeholder,
    # in modo che i futuri caratteri \n non vengano trasformati in \\n.
    content = content.replace('\\', '\\\\')
    content = content.replace('"', '\\"')

    # 4. Pulizia spazi bianchi e conversione placeholder
    
    # 4a. Sostituisce il placeholder con il vero carattere di newline (\n)
    # Questo è il punto critico: \n viene inserito dopo l'escape di \
    content = content.replace(NEWLINE_PLACEHOLDER, '\n')
    
    # 4b. Pulisci spazi orizzontali multipli
    content = re.sub(r'[ \t]{2,}', ' ', content)
    
    # 4c. Pulisci a capo multipli (massimo due per separare i paragrafi)
    content = re.sub(r'\n{3,}', '\n\n', content).strip()
    
    return content

# Assicurati che l'input sia fornito
if len(sys.argv) < 3:
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
    # L'output contiene i veri caratteri \n non escapati.
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