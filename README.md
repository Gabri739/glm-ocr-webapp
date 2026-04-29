# GLM OCR PDF Converter

Webapp per convertire PDF (anche scansioni) in Markdown pulito usando il modello GLM OCR via Ollama.

## Requisiti

1. **Ollama** installato e in esecuzione
2. **Modello GLM OCR** scaricato:
   ```bash
   ollama pull glm-ocr:latest
   ```
3. **Python 3.10+**

## Installazione

```bash
# Clona il repository
cd glm-ocr-pdf

# Crea ambiente virtuale
python -m venv venv

# Attiva (Windows)
venv\Scripts\activate
# o (macOS/Linux)
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt
```

## Avvio

1. **Avvia Ollama**:
   ```bash
   ollama serve
   ```

2. **Avvia il server web** (in un altro terminale):
   ```bash
   python main.py
   ```

3. **Apri il browser** all'indirizzo:
   ```
   http://localhost:8000
   ```

## Caratteristiche

- 📄 **Upload PDF**: Carica qualsiasi PDF, anche scansioni
- 🖼️ **Vista affiancata**: PDF originale a sinistra, Markdown a destra
- 📝 **OCR con GLM**: Utilizza il modello GLM-OCR via Ollama
- 📊 **Supporto tabelle**: Riconosce e converte tabelle in Markdown
- 🧮 **Formule LaTeX**: Supporta formule matematiche
- 🔄 **Navigazione**: Scorri pagina per pagina con frecce
- ✏️ **Modifica**: Correggi il Markdown generato
- 💾 **Export**: Scarica come `.md` o `.txt`

## Configurazione

Puoi configurare tramite variabili d'ambiente:

```bash
# Host Ollama (default: http://localhost:11434)
export OLLAMA_HOST=http://localhost:11434

# Modello (default: glm-ocr:latest)
export OLLAMA_MODEL=glm-ocr:latest
```

## Utilizzo

1. Clicca **"Carica PDF"** e seleziona un file
2. Il PDF viene convertito in immagini (una per pagina)
3. Clicca **"Processa tutto"** per avviare l'OCR
4. Naviga con le **frecce** per confrontare pagina per pagina
5. Clicca **"Modifica"** per correggere il Markdown
6. Esporta con **"Esporta"** → Markdown

## Shortcut Tastiera

- `←` / `→` : Pagina precedente/successiva
- `Ctrl+S` : Esporta Markdown

## Risoluzione problemi

**Ollama non trovato**: Verifica che `ollama serve` sia in esecuzione

**Modello non trovato**: Esegui `ollama pull glm-ocr:latest`

**Timeout**: PDF molto grandi o complessi possono richiedere più tempo. Il timeout è impostato a 5 minuti.