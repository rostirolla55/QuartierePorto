import sys
import os
import io
import unicodedata 

def sanitize_for_json(input_filepath):
    """
    Converte caratteri speciali, simboli e apici tipografici in forme JSON-safe, 
    esegue l'escape dei doppi apici e rimuove gli a capo.
    """
    if not os.path.exists(input_filepath):
        print(f"ERRORE: File non trovato: {input_filepath}", file=sys.stderr) 
        return ""

    try:
        # Leggiamo esplicitamente in UTF-8
        with io.open(input_filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 0. NORMALIZZAZIONE UNICODE
        content = unicodedata.normalize('NFC', content) 

        # 1. CONVERSIONE CARATTERI SPECIALI
        
        # Simbolo di Grado (°) in entità HTML
        content = content.replace('°', '&deg;') 
        
        # Punti di Sospensione (ellissi) in tre punti standard
        content = content.replace('…', '...') 
        
        # Trattini lunghi in trattino standard (-)
        content = content.replace('–', '-') 
        content = content.replace('—', '-') 
        
        # Smart Quotes in apici standard (") e (')
        content = content.replace('“', '"') 
        content = content.replace('”', '"')
        content = content.replace('‘', "'") 
        content = content.replace('’', "'") 
        
        # 2. ESCAPE DOPPI APICI STANDARD (")
        sanitized_content = content.replace('"', '\\\\"') 
        
        # 3. Normalizzazione degli accenti con Entità HTML (per massima sicurezza)
        # --- Nuove aggiunte per hex(D9), DA, DB, DC, DD ---
        sanitized_content = sanitized_content.replace('Ù', '&Ugrave;') # D9
        sanitized_content = sanitized_content.replace('Ú', '&Uacute;') # DA
        sanitized_content = sanitized_content.replace('Û', '&Ucirc;')  # DB
        sanitized_content = sanitized_content.replace('Ü', '&Uuml;')   # DC
        sanitized_content = sanitized_content.replace('Ý', '&Yacute;') # DD
        
        # --- Accenti già gestiti ---
        sanitized_content = sanitized_content.replace('À', '&Agrave;')
        sanitized_content = sanitized_content.replace('à', '&agrave;')
        sanitized_content = sanitized_content.replace('è', '&egrave;')
        sanitized_content = sanitized_content.replace('ì', '&igrave;')
        sanitized_content = sanitized_content.replace('ò', '&ograve;')
        sanitized_content = sanitized_content.replace('ù', '&ugrave;')
        sanitized_content = sanitized_content.replace('é', '&eacute;')
        
        # 4. Eliminazione di tutti i caratteri di a capo per una singola riga
        sanitized_content = sanitized_content.replace('\r\n', ' ')
        sanitized_content = sanitized_content.replace('\n', ' ')
        
        # Pulizia finale degli spazi
        sanitized_content = " ".join(sanitized_content.split()).strip()
        
        return sanitized_content

    except Exception as e:
        print(f"Si è verificato un errore durante l'elaborazione del file: {e}", file=sys.stderr)
        return ""

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python sanitize_text.py <percorso_del_file_html>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    result = sanitize_for_json(input_file)
    
    # Stampa solo il risultato finale su stdout per la redirezione nel file batch
    print(result)