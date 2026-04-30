import asyncio
import base64
import json
import os
import shutil
import uuid
from pathlib import Path

import fitz  # PyMuPDF
import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

# Configurazione
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "glm-ocr:latest")
OCR_PROMPT = os.environ.get(
    "OCR_PROMPT",
    "Extract all content from this document image and output clean, well-formatted Markdown. "
    "Preserve headings, paragraphs, lists, and tables (use Markdown table syntax). "
    "Describe figures concisely in italics. Do not add commentary; return only the Markdown."
)

RENDER_DPI = int(os.environ.get("RENDER_DPI", "150"))

# Directory
BASE_DIR = Path(__file__).parent.resolve()
JOBS_DIR = BASE_DIR / "jobs"
STATIC_DIR = BASE_DIR / "static"
JOBS_DIR.mkdir(exist_ok=True)

# App
app = FastAPI(title="GLM-OCR WebApp")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _job_dir(job_id: str) -> Path:
    safe = "".join(c for c in job_id if c.isalnum() or c in "-_")
    if safe != job_id or not safe:
        raise HTTPException(status_code=400, detail="invalid job id")
    p = JOBS_DIR / safe
    if not p.exists():
        raise HTTPException(status_code=404, detail="job not found")
    return p


def _render_pdf_to_pngs(pdf_path: Path, out_dir: Path) -> int:
    doc = fitz.open(pdf_path)
    try:
        zoom = RENDER_DPI / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(out_dir / f"page-{i:04d}.png")
        return doc.page_count
    finally:
        doc.close()


def _save_image_as_page(src: Path, out_dir: Path) -> int:
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.save(out_dir / "page-0001.png", format="PNG")
    return 1


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="missing filename")
    suffix = Path(file.filename).suffix.lower()
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {suffix}")

    job_id = uuid.uuid4().hex[:12]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir()
    src_path = job_dir / f"source{suffix}"

    with src_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        if suffix == ".pdf":
            n_pages = _render_pdf_to_pngs(src_path, job_dir)
        else:
            n_pages = _save_image_as_page(src_path, job_dir)
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"failed to render: {e}")

    meta = {"job_id": job_id, "filename": file.filename, "pages": n_pages}
    (job_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return meta


@app.get("/api/page/{job_id}/{page}")
async def get_page_image(job_id: str, page: int):
    job_dir = _job_dir(job_id)
    img = job_dir / f"page-{page:04d}.png"
    if not img.exists():
        raise HTTPException(status_code=404, detail="page not found")
    return FileResponse(img, media_type="image/png")


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    job_dir = _job_dir(job_id)
    meta_file = job_dir / "meta.json"
    if not meta_file.exists():
        raise HTTPException(status_code=404, detail="meta missing")
    return JSONResponse(content=json.loads(meta_file.read_text(encoding="utf-8")))


@app.get("/api/ocr/{job_id}/{page}")
async def ocr_page(job_id: str, page: int, refresh: bool = False):
    """Run OCR and stream incremental Markdown chunks as text/event-stream."""
    job_dir = _job_dir(job_id)
    img_path = job_dir / f"page-{page:04d}.png"
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="page not found")

    cache_path = job_dir / f"page-{page:04d}.md"
    if cache_path.exists() and not refresh:
        cached = cache_path.read_text(encoding="utf-8")

        async def cached_stream():
            yield f"event: cached\ndata: {json.dumps({'cached': True})}\n\n"
            yield f"data: {json.dumps({'chunk': cached})}\n\n"
            yield f"event: done\ndata: {json.dumps({'ok': True})}\n\n"

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    img_b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": OCR_PROMPT,
        "images": [img_b64],
        "stream": True,
        "options": {
            "temperature": 0.0,
            "num_predict": 8192,
        },
    }

    async def gen():
        collected: list[str] = []
        try:
            timeout = httpx.Timeout(connect=10.0, read=600.0, write=60.0, pool=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", f"{OLLAMA_URL}/api/generate", json=payload) as resp:
                    if resp.status_code != 200:
                        body = (await resp.aread()).decode("utf-8", errors="replace")
                        err = {"error": f"Ollama HTTP {resp.status_code}", "body": body[:500]}
                        yield f"event: error\ndata: {json.dumps(err)}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        chunk = obj.get("response", "")
                        if chunk:
                            collected.append(chunk)
                            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                        if obj.get("done"):
                            break
        except httpx.RequestError as e:
            yield f"event: error\ndata: {json.dumps({'error': f'Connection error: {str(e)}'})}\n\n"
            return
        except asyncio.CancelledError:
            raise

        full = "".join(collected)
        if full.strip():
            cache_path.write_text(full, encoding="utf-8")
        yield f"event: done\ndata: {json.dumps({'ok': True, 'length': len(full)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/markdown/{job_id}/{page}")
async def get_markdown(job_id: str, page: int):
    job_dir = _job_dir(job_id)
    cache_path = job_dir / f"page-{page:04d}.md"
    if not cache_path.exists():
        raise HTTPException(status_code=404, detail="not yet processed")
    return JSONResponse({"page": page, "markdown": cache_path.read_text(encoding="utf-8")})


@app.get("/api/markdown/{job_id}")
async def get_full_markdown(job_id: str):
    job_dir = _job_dir(job_id)
    meta = json.loads((job_dir / "meta.json").read_text(encoding="utf-8"))
    parts: list[str] = []
    for i in range(1, meta["pages"] + 1):
        cache_path = job_dir / f"page-{i:04d}.md"
        if cache_path.exists():
            parts.append(f"<!-- Page {i} -->\n\n" + cache_path.read_text(encoding="utf-8"))
        else:
            parts.append(f"<!-- Page {i} not processed yet -->")
    return JSONResponse({"job_id": job_id, "markdown": "\n\n---\n\n".join(parts)})


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    job_dir = _job_dir(job_id)
    shutil.rmtree(job_dir, ignore_errors=True)
    return JSONResponse({"ok": True})


@app.get("/api/health")
async def health_check():
    """Check se Ollama è raggiungibile e glm-ocr disponibile"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                has_glm = any("glm-ocr" in m.get("name", "") for m in models)
                return {
                    "status": "healthy",
                    "ollama_connected": True,
                    "ollama_url": OLLAMA_URL,
                    "glm_ocr_available": has_glm,
                    "model": OLLAMA_MODEL
                }
    except Exception:
        pass

    return {
        "status": "unhealthy",
        "ollama_connected": False,
        "glm_ocr_available": False,
        "ollama_url": OLLAMA_URL
    }


# =============================================================================
# FRONTEND
# =============================================================================

@app.get("/")
async def root():
    """Serve la webapp HTML"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    return JSONResponse({"error": "Frontend not found. Static files missing."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)