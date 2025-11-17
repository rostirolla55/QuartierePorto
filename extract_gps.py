import sys
from PIL import Image
from PIL.ExifTags import TAGS

# La funzione che converte il formato DMS (gradi, minuti, secondi)
# in formato decimale standard.
def convert_to_degrees(value):
    """
    Converte la tupla EXIF (gradi, minuti, secondi) in gradi decimali.
    """
    d = float(value[0][0]) / float(value[0][1])
    m = float(value[1][0]) / float(value[1][1])
    s = float(value[2][0]) / float(value[2][1])
    return d + (m / 60.0) + (s / 3600.0)

def extract_gps_data(image_path):
    """
    Estrae i dati GPS da un'immagine e li stampa nel formato richiesto dal batch.
    """
    try:
        image = Image.open(image_path)
    except FileNotFoundError:
        # Se l'immagine non esiste, non stampa nulla e lo script batch fallira' (ERRORLEVEL 1)
        sys.exit(1)
    except Exception as e:
        # Errore generico (es. formato non valido)
        sys.exit(1)

    exif_data = {}
    
    # 1. Ottiene tutti i dati EXIF
    try:
        info = image._getexif()
    except AttributeError:
        # L'immagine non ha dati EXIF
        print("ERRORE: Immagine senza dati EXIF.", file=sys.stderr)
        sys.exit(1)
        
    if not info:
        print("ERRORE: Immagine senza dati EXIF.", file=sys.stderr)
        sys.exit(1)

    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        exif_data[decoded] = value

    # 2. Estrae i dati GPS specifici
    gps_info = exif_data.get('GPSInfo')
    if not gps_info:
        print("ERRORE: Dati GPS (Geo-Tag) non trovati nell'immagine.", file=sys.stderr)
        sys.exit(1)

    # Decodifica le chiavi numeriche di GPSInfo in nomi leggibili
    decoded_gps = {}
    for key, value in gps_info.items():
        sub_decoded = TAGS.get(key, key)
        decoded_gps[sub_decoded] = value

    # 3. Processa e formatta le coordinate
    
    # Latitudine
    gps_latitude = decoded_gps.get('GPSLatitude')
    gps_latitude_ref = decoded_gps.get('GPSLatitudeRef')
    
    # Longitudine
    gps_longitude = decoded_gps.get('GPSLongitude')
    gps_longitude_ref = decoded_gps.get('GPSLongitudeRef')

    if gps_latitude and gps_longitude:
        lat = convert_to_degrees(gps_latitude)
        lon = convert_to_degrees(gps_longitude)
        
        # Correggi il segno (N/S e E/W)
        if gps_latitude_ref != 'N':
            lat = -lat
        if gps_longitude_ref != 'E':
            lon = -lon
            
        # 4. Stampa l'output nel formato richiesto dal batch
        # Il batch si aspetta: LAT=X.XXX\nLON=Y.YYY
        print(f"LAT={lat}")
        print(f"LON={lon}")
        
    else:
        print("ERRORE: Coordinate GPS incomplete nell'immagine.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERRORE: Percorso immagine mancante.", file=sys.stderr)
        sys.exit(1)
        
    image_path = sys.argv[1]
    extract_gps_data(image_path)