# Convert_All.ps1
# Script PowerShell per l'elaborazione completa di conversione DOCX -> HTML.

# Abilita la modalità "Stop" in caso di errore non fatale su un cmdlet
$ErrorActionPreference = "Stop"

# --- VARIABILI DI CONFIGURAZIONE ---
$PAGE_ID = "pioggia3"
$DOCX_FILE = "pioggia3.docx"
$HTML_OUTPUT_FILE = "$PAGE_ID.html"
$RAW_OUTPUT_FILE = "raw_output.html"
$DOCX_DIR = "DOCS_DA_CONVERTIRE"
# Ottiene la directory dello script corrente per definire la ROOT_DIR
$ROOT_DIR = (Get-Item -Path $PSScriptRoot -ErrorAction Stop).FullName


Write-Host "=================================================="
Write-Host "Inizio elaborazione completa per $PAGE_ID"
Write-Host "=================================================="

# Usa un blocco try/finally per garantire che la pulizia finale venga eseguita
try {
    # --- 1. ESTRAZIONE IMMAGINI (Eseguito dalla root) ---
    Write-Host "Esecuzione di extract_images.py per estrarre immagini..."
    # L'operatore '&' esegue un comando esterno. $LASTEXITCODE conterrà il codice di uscita di Python.
    & python extract_images.py $PAGE_ID $DOCX_FILE
    if ($LASTEXITCODE -ne 0) {
        throw "ERRORE: Script extract_images.py fallito (Codice di uscita: $LASTEXITCODE)."
    }

    # --- 2. ENTRA NELLA CARTELLA DI LAVORO ---
    Write-Host "Cambio directory in $DOCX_DIR..."
    Set-Location -Path $DOCX_DIR
    
    # --- 3. CHIAMATA A convert_step.bat ---
    Write-Host "Chiamata a convert_step.bat per la conversione DOCX->HTML..."
    # Esegue il file .bat (che si presume sia nella ROOT_DIR)
    & "$ROOT_DIR\convert_step.bat"
    if ($LASTEXITCODE -ne 0) {
        throw "ERRORE: La conversione con LibreOffice (via convert_step) è fallita (Codice di uscita: $LASTEXITCODE)."
    }

    # --- 4. RINOMINA E PREPARAZIONE HTML GREZZO (Locale) ---
    Write-Host "DEBUG: Tentativo di rinomina locale: $HTML_OUTPUT_FILE -> $RAW_OUTPUT_FILE"

    # Usa Rename-Item, che fallisce se il file non esiste (e innesca il catch grazie a $ErrorActionPreference)
    Rename-Item -Path $HTML_OUTPUT_FILE -NewName $RAW_OUTPUT_FILE
    Write-Host "Rinomina completata."

    # --- 5. RITORNA ALLA ROOT PER ESEGUIRE IL PYTHON SCRIPT ---
    Write-Host "Ritorno alla directory principale..."
    Set-Location -Path $ROOT_DIR

    # --- 6. POST-PROCESSO ---
    Write-Host "Esecuzione di post_process_html.py, leggendo da $DOCX_DIR..."
    & python post_process_html.py $PAGE_ID "it" $DOCX_DIR
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "AVVISO: Script post_process_html.py fallito, ma la pulizia proseguirà."
        # Non lanciamo throw qui, come nell'originale .bat, ma segnaliamo un warning.
    }

}
catch {
    # Questo blocco viene eseguito se un errore (un throw o un errore da cmdlet/Python) si verifica nel blocco try.
    Write-Error $_.Exception.Message
    # L'elaborazione si ferma qui, ma si procede al 'finally'.
}
finally {
    # --- 7. PULIZIA FINALE ---
    Write-Host "Pulizia dei file temporanei e residui in $DOCX_DIR..."
    
    # Rimuove il file RAW che serve solo al Python
    Remove-Item -Path "$DOCX_DIR\$RAW_OUTPUT_FILE" -Force -ErrorAction SilentlyContinue
    
    # Rimuove immagini temporanee (JPG e PNG) create durante la conversione
    Remove-Item -Path "$DOCX_DIR\$PAGE_ID*.jpg" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$DOCX_DIR\$PAGE_ID*.png" -Force -ErrorAction SilentlyContinue

    Write-Host "Pulizia completata."

    Write-Host "=================================================="
    Write-Host "Elaborazione $PAGE_ID COMPLETATA (Verificare eventuali errori sopra)."
    Write-Host "=================================================="
}