"""
Backend FastAPI per OCR PDF con GLM-OCR via Ollama
"""
import os
import base64
import json
import httpx
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import fitz  # PyMuPDF
from PIL import Image
import io

app = FastAPI(title="GLM OCR PDF Converter", version="1.0.0")

# CORS per permettere al frontend di comunicare
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "glm-ocr:latest")


def pdf_to_images(pdf_bytes: bytes, dpi: int = 150) -> List[bytes]:
    """
    Converte un PDF in lista di immagini (una per pagina)
    Restituisce lista di bytes PNG
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Aumenta la risoluzione per OCR migliore
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)

        # Converti in PIL Image e poi in bytes PNG
        img_data = pix.tobytes("png")
        images.append(img_data)

    doc.close()
    return images


def image_to_base64(image_bytes: bytes) -> str:
    """Converte bytes immagine in base64"""
    return base64.b64encode(image_bytes).decode('utf-8')


async def call_glm_ocr(image_base64: str, timeout: int = 300) -> str:
    """
    Chiama Ollama con GLM OCR per estrarre markdown dall'immagine
    """
    url = f"{OLLAMA_HOST}/api/generate"

    # Costruisci il prompt per OCR ottimale
    prompt = "Estrai tutto il contenuto testuale da questa immagine in formato markdown. \
Se ci sono tabelle, convertile in markdown tables. \
Se ci sono formule matematiche, usa LaTeX. \
Restituisci solo il markdown pulito senza spiegazioni."

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Ollama request timed out")
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Cannot connect to Ollama at {OLLAMA_HOST}. Is Ollama running?"
            )
        except httpx.HTTPStatusError as e:
            error_body = ""
            try:
                error_body = e.response.text
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Ollama error {e.response.status_code}: {error_body or str(e)}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Riceve il PDF, converte in immagini e restituisce preview
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        contents = await file.read()
        images = pdf_to_images(contents)

        # Converte immagini in base64 per preview
        image_previews = [image_to_base64(img) for img in images]

        return JSONResponse({
            "filename": file.filename,
            "total_pages": len(images),
            "images": image_previews
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing error: {str(e)}")


@app.post("/api/ocr/{page_index}")
async def process_ocr(page_index: int, request: Request):
    """
    Processa OCR per una specifica pagina
    """
    try:
        data = await request.json()
        image_base64 = data.get("image")
        if not image_base64:
            raise HTTPException(status_code=400, detail="No image provided")

        markdown = await call_glm_ocr(image_base64)

        return JSONResponse({
            "page": page_index + 1,
            "markdown": markdown
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR error: {str(e)}")


@app.post("/api/ocr-batch")
async def process_ocr_batch(request: Request):
    """
    Processa OCR per tutte le pagine in batch
    """
    try:
        data = await request.json()
        images = data.get("images", [])
        if not images:
            raise HTTPException(status_code=400, detail="No images provided")

        results = []
        for i, img_base64 in enumerate(images):
            try:
                markdown = await call_glm_ocr(img_base64)
                results.append({
                    "page": i + 1,
                    "markdown": markdown,
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "page": i + 1,
                    "markdown": f"",
                    "status": "error",
                    "error": str(e)
                })

        return JSONResponse({"results": results})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch OCR error: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Check se Ollama è raggiungibile"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                has_glm = any("glm-ocr" in m.get("name", "") for m in models)
                return {
                    "status": "healthy",
                    "ollama_connected": True,
                    "glm_ocr_available": has_glm
                }
    except:
        pass

    return {
        "status": "unhealthy",
        "ollama_connected": False,
        "glm_ocr_available": False
    }


# Serve il frontend statico
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)