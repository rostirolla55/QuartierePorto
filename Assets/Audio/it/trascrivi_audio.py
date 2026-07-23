import os
import sys
from openai import OpenAI

def trascrivi_file_audio(percorso_audio):
    # 1. Controlla se il file audio esiste davvero
    if not os.path.exists(percorso_audio):
        print(f"Errore: Il file '{percorso_audio}' non esiste.")
        return

    print(f"Inizio l'invio di '{percorso_audio}' alle API OpenAI Whisper...")

    try:
        # 2. Inizializza il client OpenAI
        # Il client preleverà automaticamente la chiave da os.environ["OPENAI_API_KEY"]
        # Se preferisci inserirla a mano, usa: client = OpenAI(api_key="TUA_API_KEY")
        client = OpenAI()

        # 3. Apre il file audio in modalità binaria
        with open(percorso_audio, "rb") as audio_file:
            # 4. Richiesta di trascrizione a Whisper (modello: whisper-1)
            trascrizione = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text"  # Restituisce direttamente il testo pulito
            )

        # 5. Genera il nome del file di testo di output (es. chiesasancarlo.txt)
        nome_base, _ = os.path.splitext(percorso_audio)
        file_output = f"{nome_base}.txt"

        # 6. Salva la trascrizione nel file di testo
        with open(file_output, "w", encoding="utf-8") as f_out:
            f_out.write(trascrizione)

        print("-" * 40)
        print(f"Trascrizione completata con successo!")
        print(f"File di testo creato: {file_output}")
        print("-" * 40)
        print("Anteprima del testo estratto:\n")
        print(trascrizione[:500] + "..." if len(trascrizione) > 500 else trascrizione)

    except Exception as e:
        print(f"\nSi è verificato un errore durante la trascrizione: {e}")

if __name__ == "__main__":
    # Controlla che l'utente abbia passato il nome del file audio da terminale
    if len(sys.argv) < 2:
        print("Uso corretto: python trascrivi_audio.py nome_del_file.mp3")
    else:
        trascrivi_file_audio(sys.argv[1])