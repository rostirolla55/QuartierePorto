import sys
import os
import piexif

def to_decimal(value, ref):
    """Converte le coordinate GPS frazionarie (Gradi/Minuti/Secondi) in decimale."""
    if not value:
        return 0.0

    # I valori sono memorizzati come tuple (numeratore, denominatore)
    degrees = value[0][0] / value[0][1]
    minutes = value[1][0] / value[1][1]
    seconds = value[2][0] / value[2][1]

    decimal_coord = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    # Se il riferimento (ref) è Sud ('S') o Ovest ('W'), la coordinata è negativa
    if ref in ['S', 'W']:
        return -decimal_coord
    return decimal_coord

def extract_gps_coords(image_path):
    """Estrae le coordinate GPS decimali da un file immagine EXIF."""
    if not os.path.exists(image_path):
        print(f"ERRORE: File immagine non trovato: {image_path}", file=sys.stderr)
        return None, None

    try:
        exif_dict = piexif.load(image_path)
    except Exception as e:
        print(f"ERRORE: Impossibile leggere i dati EXIF dal file: {e}", file=sys.stderr)
        return None, None

    # ATTENZIONE: La costante GPSIFD_TAG non è esposta direttamente.
    # Si controlla la presenza del blocco GPS (indice 'GPS' o 34853)
    # L'indice numerico del blocco GPS è 34853 (piexif.ImageIFD.GPSInfo)
    # Ma il modo più semplice è usare la chiave "GPS" che piexif usa internamente.

    if "GPS" not in exif_dict:
        print(f"ATTENZIONE: Nessun dato GPS trovato nel file: {image_path}", file=sys.stderr)
        return None, None

    gps_info = exif_dict["GPS"]  # Usiamo la chiave 'GPS'
    
    # Estrazione Latitudine
    lat_ref = gps_info.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode('ascii')
    lat_value = gps_info.get(piexif.GPSIFD.GPSLatitude)
    
    # Estrazione Longitudine
    lon_ref = gps_info.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode('ascii')
    lon_value = gps_info.get(piexif.GPSIFD.GPSLongitude)

    # Controlliamo che i valori siano effettivamente presenti
    if lat_value is None or lon_value is None:
        print(f"ATTENZIONE: I dati GPS sono presenti ma le coordinate sono incomplete.", file=sys.stderr)
        return None, None


    latitude = to_decimal(lat_value, lat_ref)
    longitude = to_decimal(lon_value, lon_ref)

    return latitude, longitude

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python extract_gps.py <percorso_del_file_immagine>", file=sys.stderr)
        sys.exit(1)
    
    image_file = sys.argv[1]
    lat, lon = extract_gps_coords(image_file)
    
    if lat is not None and lon is not None:
        # Stampa l'output su stdout per cattura con un file batch o shell
        print(f"LAT={lat:.6f}")
        print(f"LON={lon:.6f}")
        sys.exit(0)
    else:
        # Se l'estrazione fallisce, usciamo con errore
        sys.exit(1)
