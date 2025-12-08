# ----------------------------------------------------------------------------------
# Script di Orchestrazione: Convert_All.ps1
# Esegue l'intera pipeline di conversione da DOCX a HTML/JSON per una pagina
# e archivia i risultati finali nella cartella 'codice'.
# ----------------------------------------------------------------------------------

param(
    [Parameter(Mandatory=$true)]
    [string]$pageId
)

# --- INIZIO CONFIGURAZIONE ---

# 1. Definizioni di percorso e variabili
$PageID_Lower = $pageId.ToLower()
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Percorsi di lavoro
$DocsToConvertDir = Join-Path -Path $RootDir -ChildPath "DOCS_DA_CONVERTIRE"
$ArchiveRootDir = Join-Path -Path $RootDir -ChildPath "codice" # La cartella di archiviazione
$LibreOfficePath = "C:\Program Files\LibreOffice\program\soffice.exe" # Aggiorna questo percorso se necessario

# Nomi dei file di input/output
$SourceDocx = Join-Path -Path $DocsToConvertDir -ChildPath "$PageID_Lower.docx"

# FIX Rimosso il '+' esterno, utilizzando l'interpolazione stringa ${} per sicurezza.
$OutputHtml = Join-Path -Path $RootDir -ChildPath "$PageID_Lower.html"
$OutputJson = Join-Path -Path $RootDir -ChildPath "${PageID_Lower}_texts.json" 

# Percorsi assoluti degli script Python (nella $RootDir)
$ExtractImagesScript = Join-Path -Path $RootDir -ChildPath "extract_images.py"
$PostProcessScript = Join-Path -Path $RootDir -ChildPath "post_process_html.py"

# Crea la sottocartella di archiviazione con timestamp
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveSubDir = Join-Path -Path $ArchiveRootDir -ChildPath "$PageID_Lower\_$Timestamp"

# -----------------------------

Write-Host "--- Avvio Conversione DOCX a HTML (con Archiviazione) ---"
Write-Host "ID Pagina (minuscolo): $PageID_Lower"
Write-Host "File DOCX di origine: $SourceDocx"
Write-Host "Cartella Archivio: $ArchiveSubDir"
Write-Host "------------------------------------"


# 1. Verifica prerequisiti
if (-not (Test-Path $SourceDocx)) {
    Write-Error "ERRORE: File DOCX non trovato al percorso: $SourceDocx"
    exit 1
}

if (-not (Test-Path $LibreOfficePath)) {
    Write-Error "ERRORE: LibreOffice non trovato al percorso: $LibreOfficePath"
    Write-Error "Assicurati che LibreOffice sia installato e il percorso sia corretto."
    exit 1
}


# 2. Estrazione delle immagini incorporate
Write-Host "`n[FASE 1/4] Esecuzione di extract_images.py per estrarre le immagini..."
if (-not (Test-Path $ExtractImagesScript)) { Write-Error "ERRORE: Script Python non trovato: $ExtractImagesScript"; exit 1 }

# Assumiamo che $RootDir venga passato per definire la base per Assets\images
& python $ExtractImagesScript $SourceDocx $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore in extract_images.py. Interruzione."; exit 1 }


# 3. Conversione DOCX a HTML (LibreOffice)
Write-Host "`n[FASE 2/4] Conversione da DOCX a HTML tramite LibreOffice..."
& $LibreOfficePath --headless --convert-to html $SourceDocx --outdir $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore nella conversione di LibreOffice. Interruzione."; exit 1 }


# 4. Post-processamento HTML e generazione JSON/HTML finali
Write-Host "`n[FASE 3/4] Esecuzione di post_process_html.py per la pulizia e lo split..."
if (-not (Test-Path $PostProcessScript)) { Write-Error "ERRORE: Script Python non trovato: $PostProcessScript"; exit 1 }
& python $PostProcessScript $PageID_Lower $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore in post_process_html.py. Interruzione."; exit 1 }


# 5. Archiviazione dei risultati finali
Write-Host "`n[FASE 4/4] Archiviazione dei file HTML e JSON finali nella cartella 'codice'..."

# Crea la cartella di archiviazione se non esiste
New-Item -ItemType Directory -Force -Path $ArchiveSubDir | Out-Null

# Copia i file generati
try {
    # Copia il file HTML finale
    Copy-Item -Path $OutputHtml -Destination $ArchiveSubDir -Force
    Write-Host " - Copia di $PageID_Lower.html in $ArchiveSubDir riuscita."

    # Copia il file JSON finale
    if (Test-Path $OutputJson) {
        Copy-Item -Path $OutputJson -Destination $ArchiveSubDir -Force
        Write-Host " - Copia di ${PageID_Lower}_texts.json in $ArchiveSubDir riuscita."
    } else {
        Write-Warning "AVVISO: File JSON di output non trovato ($($OutputJson)). Salto la copia."
    }

} catch {
    Write-Error "ERRORE durante l'archiviazione dei file: $($_.Exception.Message)"
    # Continuiamo l'esecuzione, ma con un avviso.
}


Write-Host "`n--- Conversione e Archiviazione Completate per $PageID_Lower ---"
Write-Host "I file finali sono stati archiviati qui: $ArchiveSubDir"