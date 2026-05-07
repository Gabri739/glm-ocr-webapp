# PDF-to-MD Converter

Webapp per convertire PDF e immagini in Markdown pulito usando modelli OCR e Vision tramite Ollama.

## Caratteristiche

- **Multi-formato**: Supporta PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
- **Strategie multiple**: Scegli tra Auto, Vision, OCR o Hybrid
- **Streaming OCR**: Risultati in tempo reale mentre il modello elabora
- **Vista affiancata**: Documento originale a sinistra, Markdown a destra
- **Navigazione pagine**: Thumbnail per navigare tra le pagine
- **Caching**: Risultati salvati su disco per non rielaborare
- **Download**: Esporta tutto il documento in un file `.md`

## Strategie OCR

| Strategia | Descrizione | Quando usarla |
|-----------|-------------|---------------|
| **Auto** (default) | Usa LightOnOCR per massima qualita | Massima qualita senza pensarci |
| **Vision** | Usa direttamente il modello vision sull'immagine | Veloce, una sola chiamata |

## Requisiti

1. **Python 3.10+**
2. **Ollama** installato e in esecuzione
3. **Modello LightOnOCR** (per strategia Auto):
   ```bash
   ollama pull Maternion/LightOnOCR-2:latest
   ```
4. **Modello Vision** (per strategia Vision):
   ```bash
   ollama pull qwen3.5:397b-cloud
   ```

## Installazione

```bash
# Clona il repository
git clone <repo-url>
cd pdf-to-md-converter

# Crea ambiente virtuale (opzionale ma consigliato)
python -m venv venv

# Attiva l'ambiente virtuale
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

## Avvio

1. **Avvia Ollama** (se non e gia in esecuzione):
   ```bash
   ollama serve
   ```

2. **Avvia il server web**:
   ```bash
   python pd-to-md.py
   ```

3. **Apri il browser**:
   ```
   http://localhost:8000
   ```

## Configurazione

Variabili d'ambiente opzionali:

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | URL del server Ollama |
| `VISION_MODEL` | `qwen3.5:397b-cloud` | Modello Vision |
| `COMPLEX_MODEL` | `Maternion/LightOnOCR-2:latest` | Modello Auto (LightOnOCR) |
| `RENDER_DPI` | `150` | DPI per rendering PDF |

Esempio:
```bash
export VISION_MODEL=llava:latest
export RENDER_DPI=200
python pd-to-md.py
```

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/upload` | Carica PDF/immagine, restituisce job_id |
| `GET` | `/api/page/{job_id}/{page}` | Ottieni immagine pagina |
| `GET` | `/api/ocr/{job_id}/{page}` | Avvia OCR (streaming SSE) |
| `GET` | `/api/ocr/{job_id}/{page}?strategy=auto` | OCR con strategia Auto |
| `GET` | `/api/ocr/{job_id}/{page}?strategy=vision` | OCR con strategia Vision |
| `GET` | `/api/markdown/{job_id}` | Scarica tutto il markdown |
| `GET` | `/api/health` | Stato connessione Ollama e modelli |
| `DELETE` | `/api/jobs/{job_id}` | Elimina job |

## Streaming Events (SSE)

L'endpoint `/api/ocr/{job_id}/{page}` utilizza Server-Sent Events:

| Evento | Descrizione |
|--------|-------------|
| `cached` | Risultato gia in cache |
| `stage` | Cambio passata (ocr -> vision in hybrid) |
| `data` | Chunk di testo generato |
| `done` | Elaborazione completata |
| `error` | Errore durante l'elaborazione |

## Struttura Progetto

```
glm-ocr-webapp/
├── pd-to-md.py          # Backend FastAPI
├── requirements.txt     # Dipendenze Python
├── static/
│   ├── index.html      # Frontend HTML
│   ├── app.js          # Logica frontend
│   └── styles.css      # Stili CSS
├── jobs/               # Directory job (auto-creata)
│   └── {job_id}/
│       ├── meta.json   # Metadati job
│       ├── page-*.png  # Immagini pagine
│       └── page-*.md   # Risultati OCR (cache)
└── uploads/            # Upload temporanei
```

## Keyboard Shortcuts

- `<-` / `->` : Naviga tra le pagine
- `Ctrl+S` / `Cmd+S` : Scarica Markdown
- `Escape` : Torna alla schermata upload

## Troubleshooting

### Ollama non trovato
```bash
# Verifica che Ollama sia in esecuzione
ollama list

# Se non parte
ollama serve
```

### Modello non trovato
```bash
# Scarica i modelli necessari
ollama pull Maternion/LightOnOCR-2:latest
ollama pull qwen3.5:397b-cloud
```

### Timeout su documenti grandi
Il timeout e impostato a 10 minuti. Per documenti molto lunghi, puoi aumentare `RENDER_DPI` per qualita migliore o diminuirlo per performance migliori.

### Caricamento infinito
Se l'OCR sembra bloccato, verifica:
1. Che Ollama sia in esecuzione: `ollama list`
2. Che il modello sia disponibile: controlla `/api/health`
3. Prova la strategia "vision" invece di "hybrid" per testare

## Licenza

MIT
