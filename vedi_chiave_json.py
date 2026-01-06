import json
import os
import sys

def vedi_chiave_json(page_id, key_name, root_dir="."):
    """
    Legge i file texts.json nelle diverse lingue ed estrae il valore di una chiave specifica.
    """
    languages = ["it", "en", "es", "fr"]
    results = []

    print(f"--- Ricerca per Pagina: '{page_id}' | Chiave: '{key_name}' ---\n")

    for lang in languages:
        # Costruzione del percorso dinamico
        json_path = os.path.join(root_dir, 'data', 'translations', lang, 'texts.json')
        
        if not os.path.exists(json_path):
            results.append(f"[{lang}] ❌ File non trovato: {json_path}")
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Controllo se l'ID pagina esiste nel JSON
            if page_id in data:
                page_data = data[page_id]
                # Controllo se la chiave esiste nel blocco della pagina
                if key_name in page_data:
                    valore = page_data[key_name]
                    # Formattazione richiesta: "id"; "chiave": "valore"
                    results.append(f"[{lang}] \"{page_id}\"; \"{key_name}\": \"{valore}\"")
                else:
                    results.append(f"[{lang}] ⚠️ Chiave '{key_name}' non presente in '{page_id}'")
            else:
                results.append(f"[{lang}] ⚠️ Pagina '{page_id}' non trovata")
                
        except json.JSONDecodeError:
            results.append(f"[{lang}] ❌ Errore di decodifica JSON in {json_path}")
        except Exception as e:
            results.append(f"[{lang}] ❌ Errore imprevisto: {str(e)}")

    # Stampa i risultati
    for res in results:
        print(res)

if __name__ == "__main__":
    # Controllo argomenti da riga di comando
    if len(sys.argv) < 3:
        print("Uso: python vedi_chiave_json.py <page_id> <key_name> [root_path]")
        print("Esempio: python vedi_chiave_json.py cavaticcio audioSource")
        sys.exit(1)

    p_id = sys.argv[1]
    k_name = sys.argv[2]
    # Se passi il percorso root come terzo argomento, lo usa, altrimenti usa la cartella corrente
    r_path = sys.argv[3] if len(sys.argv) > 3 else "."

    vedi_chiave_json(p_id, k_name, r_path)