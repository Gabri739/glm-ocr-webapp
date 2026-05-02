# GLM-OCR WebApp

Webapp per convertire PDF e immagini in Markdown pulito usando modelli OCR e Vision tramite Ollama.

## Caratteristiche

- **Multi-formato**: Supporta PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
- **Strategie multiple**: Scegli tra Vision, OCR o Hybrid
- **Streaming OCR**: Risultati in tempo reale mentre il modello elabora
- **Vista affiancata**: Documento originale a sinistra, Markdown a destra
- **Navigazione pagine**: Thumbnail per navigare tra le pagine
- **Caching**: Risultati salvati su disco per non rielaborare
- **Download**: Esporta tutto il documento in un file `.md`

## Strategie OCR

| Strategia | Descrizione | Quando usarla |
|-----------|-------------|---------------|
| **Vision** (default) | Usa direttamente il modello vision sull'immagine | Veloce, una sola chiamata |
| **OCR** | Usa solo glm-ocr | Testo stampato chiaro, massima velocita |
| **Hybrid** | Prima passata OCR, poi correzione Vision | Documenti complessi (tabelle, formule) |

## Requisiti

1. **Python 3.10+**
2. **Ollama** installato e in esecuzione
3. **Modello GLM-OCR** scaricato:
   ```bash
   ollama pull glm-ocr:latest
   ```
4. **Modello Vision** (opzionale, per strategia hybrid/vision):
   ```bash
   ollama pull qwen3.5:397b-cloud
   ```

## Installazione

```bash
# Clona il repository
git clone <repo-url>
cd glm-ocr-webapp

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
   python main.py
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
| `OLLAMA_MODEL` | `glm-ocr:latest` | Modello OCR |
| `VISION_MODEL` | `qwen3.5:397b-cloud` | Modello Vision (hybrid/vision) |
| `OCR_PROMPT` | *(vedi codice)* | Prompt per l'OCR |
| `VISION_PROMPT` | *(vedi codice)* | Prompt per la correzione Vision |
| `RENDER_DPI` | `150` | DPI per rendering PDF |

Esempio:
```bash
export VISION_MODEL=llava:latest
export RENDER_DPI=200
python main.py
```

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/upload` | Carica PDF/immagine, restituisce job_id |
| `GET` | `/api/page/{job_id}/{page}` | Ottieni immagine pagina |
| `GET` | `/api/ocr/{job_id}/{page}` | Avvia OCR (streaming SSE) |
| `GET` | `/api/ocr/{job_id}/{page}?strategy=vision` | OCR con strategia |
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
├── main.py              # Backend FastAPI
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
ollama pull glm-ocr:latest
ollama pull qwen3.5:397b-cloud
```

### Timeout su documenti grandi
Il timeout è impostato a 10 minuti. Per documenti molto lunghi, puoi aumentare `RENDER_DPI` per qualità migliore o diminuirlo per performance migliori.

### Caricamento infinito
Se l'OCR sembra bloccato, verifica:
1. Che Ollama sia in esecuzione: `ollama list`
2. Che il modello sia disponibile: controlla `/api/health`
3. Prova la strategia "vision" invece di "hybrid" per testare

## Licenza

MIT
