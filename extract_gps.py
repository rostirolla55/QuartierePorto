import sys
import piexif

def convert_to_degrees(value, reference):
    """
    Converte la tupla EXIF (gradi, minuti, secondi) in gradi decimali.
    Riceve il valore (una lista di frazioni) e il riferimento (N, S, E, W).
    """
    try:
        # piexif usa tupla di (numeratore, denominatore) per le frazioni
        d = value[0][0] / value[0][1]
        m = value[1][0] / value[1][1]
        s = value[2][0] / value[2][1]
    except ZeroDivisionError:
        return 0.0
    except IndexError:
        # Gestisce tuple incomplete
        return 0.0

    degrees = d + (m / 60.0) + (s / 3600.0)

    # Applica il segno in base al riferimento (Sud o Ovest)
    if reference in ('S', 'W'):
        degrees = -degrees
        
    return degrees

def extract_gps_data(image_path):
    """
    Estrae i dati GPS da un'immagine usando piexif.
    """
    try:
        exif_dict = piexif.load(image_path)
    except FileNotFoundError:
        print("ERRORE: Immagine non trovata.", file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("ERRORE: Impossibile leggere i dati EXIF dall'immagine.", file=sys.stderr)
        sys.exit(1)

    # Il blocco GPS è memorizzato sotto la chiave 'GPS' nel dizionario
    if piexif.GPSIFD not in exif_dict:
        print("ERRORE: Dati GPS (Geo-Tag) non trovati nell'immagine.", file=sys.stderr)
        sys.exit(1)
        
    gps_info = exif_dict[piexif.GPSIFD]

    # Controlla se esistono i tag necessari (Latitudine, Longitudine e Riferimenti)
    tag_lat = piexif.GPSIFD.GPSLatitude
    tag_lon = piexif.GPSIFD.GPSLongitude
    tag_lat_ref = piexif.GPSIFD.GPSLatitudeRef
    tag_lon_ref = piexif.GPSIFD.GPSLongitudeRef

    if not all(t in gps_info for t in [tag_lat, tag_lon, tag_lat_ref, tag_lon_ref]):
        print("ERRORE: Coordinate GPS incomplete nell'immagine (mancano Lat/Lon o riferimenti).", file=sys.stderr)
        sys.exit(1)

    try:
        # Conversione e stampa
        lat_ref = gps_info[tag_lat_ref].decode('ascii').strip()
        lon_ref = gps_info[tag_lon_ref].decode('ascii').strip()
        
        lat = convert_to_degrees(gps_info[tag_lat], lat_ref)
        lon = convert_to_degrees(gps_info[tag_lon], lon_ref)

        # Stampa l'output nel formato richiesto dal batch
        print(f"LAT={lat}")
        print(f"LON={lon}")
        
    except Exception as e:
        print(f"ERRORE durante la conversione delle coordinate: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    image_path = sys.argv[1]
    extract_gps_data(image_path)