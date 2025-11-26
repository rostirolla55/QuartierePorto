import sys
import re
import html

def sanitize_html_to_text(html_content):
    # 1. Decodifica le entity HTML (es. &egrave; -> è)
    content = html.unescape(html_content)

    # 2. Rimuovi tutti i tag HTML, lasciando solo il testo
    # Manteniamo i caratteri di a capo per preservare la struttura del testo
    content = re.sub(r'</p>', '\n', content)
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'<[^>]*>', '', content)

    # 3. Pulisci spazi bianchi multipli e a capo
    content = re.sub(r'\s{2,}', ' ', content) # Sostituisce spazi multipli con uno spazio singolo
    content = re.sub(r'\n{2,}', '\n\n', content).strip() # Sostituisce a capo multipli
    
    # 4. JSON Escape (necessario per inserimento diretto nel JSON)
    content = content.replace('\\', '\\\\')
    content = content.replace('"', '\\"')
    content = content.replace('\n', '\\n')

    # Aggiungi un punto (o un simbolo) per rappresentare la fine di un blocco di testo se necessario
    # Ad esempio, per la visualizzazione a blocchi, ma di solito si vuole solo il testo pulito.
    # Non aggiungiamo nulla per mantenere l'output il più fedele possibile.
    
    return content

# Assicurati che l'input sia fornito
if len(sys.argv) < 2:
    print("ERRORE: Devi passare il nome del file HTML da sanificare come argomento.")
    sys.exit(1)

input_filename = sys.argv[1]
output_filename = input_filename.replace('.html', '.txt')

try:
    # Apri il file HTML di input
    # Usiamo 'r' per la lettura e specifichiamo 'utf-8' in lettura, che è un buon standard
    with open(input_filename, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Sanificazione
    sanitized_text = sanitize_html_to_text(html_content)

    # Scrivi il testo sanificato nel file di output
    # CRUCIALE: Usiamo 'w' per la scrittura e specifichiamo 'utf-8' per gestire gli emoji e i caratteri speciali
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(sanitized_text)
    
    print(f"Testo sanificato con successo.")
    print(f"Contenuto salvato in: {output_filename}")

except FileNotFoundError:
    print(f"ERRORE: File di input non trovato: {input_filename}")
    sys.exit(1)
except Exception as e:
    # Se l'errore Unicode persiste, lo catturiamo e lo stampiamo qui
    print(f"ERRORE durante l'elaborazione del file: {e}")
    sys.exit(1)