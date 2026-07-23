import os
import json

# --- CONFIGURAZIONI ---
LANGUAGES = ["it", "en", "es", "fr"]

def sync_labels():
    # Determina la root (cartella superiore a quella dello script o corrente)
    root = os.getcwd()
    
    print(f"Avvio sincronizzazione etichette menu dalla cartella: {root}")

    for lang in LANGUAGES:
        texts_path = os.path.join(root, "data", "translations", lang, "texts.json")
        nav_json_path = os.path.join(root, "menu_json", f"nav-{lang}.json")

        # Verifichiamo l'esistenza di entrambi i file per la lingua corrente
        if not os.path.exists(texts_path):
            print(f" [!] Saltato {lang}: texts.json non trovato in {texts_path}")
            continue
        if not os.path.exists(nav_json_path):
            print(f" [!] Saltato {lang}: nav-{lang}.json non trovato in {nav_json_path}")
            continue

        try:
            # 1. Carica le traduzioni
            with open(texts_path, "r", encoding="utf-8") as f:
                texts_data = json.load(f)
            
            nav_translations = texts_data.get("nav", {})
            if not nav_translations:
                print(f" [?] Lingua {lang}: Nessun blocco 'nav' trovato in texts.json")
                continue

            # 2. Carica la struttura del menu
            with open(nav_json_path, "r", encoding="utf-8") as f:
                nav_structure = json.load(f)

            # Supporto sia per lista diretta [] che per oggetto {"items": []}
            is_object_format = isinstance(nav_structure, dict) and "items" in nav_structure
            items = nav_structure["items"] if is_object_format else nav_structure

            updated_count = 0
            # 3. Aggiorna i testi nel menu usando le chiavi di texts.json
            for item in items:
                item_id = item.get("id")
                if item_id in nav_translations:
                    old_text = item.get("text", "")
                    new_text = nav_translations[item_id]
                    
                    if old_text != new_text:
                        item["text"] = new_text
                        updated_count += 1

            # 4. Salva il file nav-[lang].json aggiornato
            if updated_count > 0:
                with open(nav_json_path, "w", encoding="utf-8") as f:
                    json.dump(nav_structure, f, indent=4, ensure_ascii=False)
                print(f" [+] {lang.upper()}: Aggiornate {updated_count} etichette nel menu.")
            else:
                print(f" [.] {lang.upper()}: Menu già sincronizzato.")

        except Exception as e:
            print(f" [!] Errore durante l'elaborazione della lingua {lang}: {e}")

if __name__ == "__main__":
    sync_labels()
    print("\nProcedura completata.")