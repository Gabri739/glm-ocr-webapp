# GLM-OCR WebApp

Webapp per convertire PDF e immagini in Markdown pulito usando il modello GLM-OCR tramite Ollama.

## Caratteristiche

- **Multi-formato**: Supporta PDF, PNG, JPG, JPEG, TIFF, BMP, WEBP
- **Streaming OCR**: Risultati in tempo reale mentre il modello elabora
- **Vista affiancata**: Documento originale a sinistra, Markdown a destra
- **Navigazione pagine**: Thumbnail per navigare tra le pagine
- **Caching**: Risultati salvati su disco per non rielaborare
- **Download**: Esporta tutto il documento in un file `.md`

## Requisiti

1. **Python 3.10+**
2. **Ollama** installato e in esecuzione
3. **Modello GLM-OCR** scaricato:
   ```bash
   ollama pull glm-ocr:latest
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

1. **Avvia Ollama** (se non è già in esecuzione):
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
| `OLLAMA_MODEL` | `glm-ocr:latest` | Modello da utilizzare |
| `OCR_PROMPT` | *(vedi codice)* | Prompt per l'OCR |
| `RENDER_DPI` | `150` | DPI per rendering PDF |

Esempio:
```bash
export OLLAMA_URL=http://192.168.1.100:11434
export RENDER_DPI=200
python main.py
```

## API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `POST` | `/api/upload` | Carica PDF/immagine, restituisce job_id |
| `GET` | `/api/page/{job_id}/{page}` | Ottieni immagine pagina |
| `GET` | `/api/ocr/{job_id}/{page}` | Avvia OCR (streaming SSE) |
| `GET` | `/api/markdown/{job_id}` | Scarica tutto il markdown |
| `GET` | `/api/health` | Stato connessione Ollama |
| `DELETE` | `/api/jobs/{job_id}` | Elimina job |

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

- `←` / `→` : Naviga tra le pagine
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
# Scarica il modello GLM-OCR
ollama pull glm-ocr:latest
```

### Timeout su documenti grandi
Il timeout è impostato a 10 minuti. Per documenti molto lunghi, puoi aumentare `RENDER_DPI` per qualità migliore o diminuirlo per performance migliori.
