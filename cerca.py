import json
import os
import sys

def cerca_nel_json():
    # Se passato come argomento da CMD, usa quello, altrimenti chiedi input
    target = sys.argv[1] if len(sys.argv) > 1 else input("Inserisci il blocco (es. carracci): ").strip()
    
    lingue = ['en', 'es', 'fr', 'it']
    base_path = "data/translations"

    for lingua in lingue:
        file_path = os.path.join(base_path, lingua, "texts.json")
        print(f"\n--- LINGUA: {lingua.upper()} ---")

        if not os.path.exists(file_path):
            print(f"File non trovato: {file_path}")
            continue

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Ricerca case-insensitive della chiave
                # Creiamo un dizionario temporaneo con chiavi minuscole per il confronto
                data_lower = {k.lower(): v for k, v in data.items()}
                
                if target.lower() in data_lower:
                    blocco = data_lower[target.lower()]
                    
                    # Se il blocco è un oggetto (dizionario), lo stampiamo riga per riga
                    if isinstance(blocco, dict):
                        for chiave, valore in blocco.items():
                            print(f"{chiave:18}: {valore}")
                    else:
                        print(blocco)
                else:
                    print(f"Blocco '{target}' non trovato nel file.")
                    
        except Exception as e:
            print(f"Errore durante la lettura: {e}")

if __name__ == "__main__":
    cerca_nel_json()