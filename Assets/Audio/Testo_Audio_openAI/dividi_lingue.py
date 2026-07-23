import os
import sys
import re

def elabora_file(percorso_file):
    # Controlla se il file esiste
    if not os.path.exists(percorso_file):
        print(f"Errore: Il file '{percorso_file}' non esiste.")
        return

    # Ricava il nome base (es. "manifattura" da "manifattura.txt")
    nome_base, _ = os.path.splitext(os.path.basename(percorso_file))
    dir_output = os.path.dirname(percorso_file) or "."

    # Legge il contenuto del file generato dalla chat
    with open(percorso_file, "r", encoding="utf-8") as f:
        contenuto = f.read()

    # Mappatura dei tag con le estensioni delle lingue
    tag_lingue = {
        r"\[ITALIANO\]": "it",
        r"\[INGLESE\]": "en",
        r"\[SPAGNOLO\]": "es",
        r"\[FRANCESE\]": "fr"
    }

    # Trova le posizioni dei tag nel testo
    posizioni = []
    for tag, lang_code in tag_lingue.items():
        match = re.search(tag, contenuto)
        if match:
            posizioni.append((match.start(), tag, lang_code))

    # Ordina i tag in base a come appaiono nel testo
    posizioni.sort()

    if not posizioni:
        print("Errore: Non ho trovato nessun tag valido ([ITALIANO], [INGLESE], ecc.) nel file.")
        return

    # Estrae il testo tra un tag e l'altro e salva i file
    for i in range(len(posizioni)):
        pos_corrente, tag_corrente, lang_corrente = posizioni[i]
        
        # L'inizio del testo è subito dopo il tag corrente
        inizio_testo = pos_corrente + len(tag_corrente.replace("\\", ""))
        
        # La fine del testo è l'inizio del tag successivo, oppure la fine del file
        if i + 1 < len(posizioni):
            fine_testo = posizioni[i+1][0]
        else:
            fine_testo = len(contenuto)
            
        testo_estratto = contenuto[inizio_testo:fine_testo].strip()
        
        # Genera il nuovo nome file (es. manifattura-it.txt)
        nuovo_nome_file = os.path.join(dir_output, f"{nome_base}-{lang_corrente}.txt")
        
        # Salva il file pulito
        with open(nuovo_nome_file, "w", encoding="utf-8") as f_out:
            f_out.write(testo_estratto)
            
        print(f"Creato file: {nuovo_nome_file} ({len(testo_estratto)} caratteri)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python dividi_lingue.py nome_del_file.txt")
    else:
        elabora_file(sys.argv[1])