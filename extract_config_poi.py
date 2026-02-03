import re
import json
import os

def extract_config_from_js():
    js_file = "main.js"
    output_file = "pois_config.json"

    if not os.path.exists(js_file):
        print(f"Errore: {js_file} non trovato.")
        return

    with open(js_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Estrazione POIS_LOCATIONS
    # Cerchiamo i pattern { id: '...', lat: ..., lon: ..., distanceThreshold: ... }
    poi_pattern = r"{\s*id:\s*'([^']*)',\s*lat:\s*([\d\.]+),\s*lon:\s*([\d\.]+),\s*distanceThreshold:\s*(\d+)\s*}"
    poi_matches = re.findall(poi_pattern, content)
    
    locations_dict = {}
    for match in poi_matches:
        poi_id, lat, lon, threshold = match
        locations_dict[poi_id] = {
            "id": poi_id,
            "lat": float(lat),
            "lon": float(lon),
            "threshold": int(threshold)
        }

    # 2. Estrazione navLinksData
    # Cerchiamo i pattern { id: '...', key: '...', base: '...' }
    nav_pattern = r"{\s*id:\s*'([^']*)',\s*key:\s*'[^']*',\s*base:\s*'([^']*)'\s*}"
    nav_matches = re.findall(nav_pattern, content)
    
    nav_dict = {}
    for match in nav_matches:
        nav_id, base_name = match
        if base_name != 'index': # Saltiamo la home per la mappatura dei POI
            nav_dict[base_name] = nav_id

    # 3. Unione dei dati
    # Associano le coordinate (locations) con i dati di navigazione (nav)
    # Usiamo l'ID della location come chiave di collegamento con il 'base' del nav
    final_pois = []
    
    for poi_id, data in locations_dict.items():
        # Cerchiamo se esiste un link di navigazione corrispondente
        # Spesso l'id del POI coincide con il 'base' del link
        nav_id = nav_dict.get(poi_id, f"nav{poi_id.capitalize()}")
        
        poi_entry = {
            "id": data["id"],
            "lat": data["lat"],
            "lon": data["lon"],
            "threshold": data["threshold"],
            "nav_id": nav_id,
            "base_name": poi_id
        }
        final_pois.append(poi_entry)

    # 4. Salvataggio in JSON
    config_data = {"pois": final_pois}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    print(f"File {output_file} generato con successo!")
    print(f"Estratti {len(final_pois)} punti di interesse.")

if __name__ == "__main__":
    extract_config_from_js()