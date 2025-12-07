# ----------------------------------------------------------------------------------
# Script di Orchestrazione: Convert_All.ps1
# Esegue l'intera pipeline di conversione da DOCX a HTML/JSON per una pagina.
# ----------------------------------------------------------------------------------

param(
    [Parameter(Mandatory=$true)]
    [string]$pageId
)

# --- INIZIO CONFIGURAZIONE ---

# Converti l'ID della pagina in minuscolo immediatamente, come richiesto.
$PageID_Lower = $pageId.ToLower()

# La cartella root è la directory in cui si trova questo script
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$UtilitiesDir = Join-Path -Path $RootDir -ChildPath "Utilities"
$PythonScriptsDir = Join-Path -Path $UtilitiesDir -ChildPath "Python_scripts"
$LibreOfficePath = "C:\Program Files\LibreOffice\program\soffice.exe" # Aggiorna questo percorso se necessario

# Nome del file DOCX da convertire (DEVE essere nella cartella root)
$SourceDocx = Join-Path -Path $RootDir -ChildPath "$PageID_Lower.docx"

# -----------------------------

Write-Host "--- Avvio Conversione DOCX a HTML ---"
Write-Host "ID Pagina (minuscolo): $PageID_Lower"
Write-Host "File DOCX di origine: $SourceDocx"
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
Write-Host "`n[FASE 1/3] Esecuzione di extract_images.py per estrarre le immagini..."
$ExtractImagesScript = Join-Path -Path $PythonScriptsDir -ChildPath "extract_images.py"
# Passa il nome del file DOCX di input come argomento
& python $ExtractImagesScript $SourceDocx $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore in extract_images.py. Interruzione."; exit 1 }


# 3. Conversione DOCX a HTML (LibreOffice)
Write-Host "`n[FASE 2/3] Conversione da DOCX a HTML tramite LibreOffice..."
# LibreOffice crea un file $PageID_Lower.html nella cartella $RootDir
& $LibreOfficePath --headless --convert-to html $SourceDocx --outdir $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore nella conversione di LibreOffice. Interruzione."; exit 1 }


# 4. Post-processamento HTML e generazione JSON/HTML finali
Write-Host "`n[FASE 3/3] Esecuzione di post_process_html.py per la pulizia e lo split..."
$PostProcessScript = Join-Path -Path $PythonScriptsDir -ChildPath "post_process_html.py"

# Passa l'ID in minuscolo allo script di post-processamento
& python $PostProcessScript $PageID_Lower $RootDir
if ($LASTEXITCODE -ne 0) { Write-Error "Errore in post_process_html.py. Interruzione."; exit 1 }


Write-Host "`n--- Conversione Completata per $PageID_Lower ---"
Write-Host "File generati in $RootDir:"
Write-Host " - $PageID_Lower.html"
Write-Host " - $PageID_Lower_texts.json (o similare)"