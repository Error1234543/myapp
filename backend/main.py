from __future__ import annotations

import io
import re
from typing import Annotated

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field
from pypdf import PdfReader, PdfWriter

APP_VERSION = "0.1.1"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 30_000_000
MAX_PDF_PAGES = 200

Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

app = FastAPI(
    title="TOOLNEX API",
    description="File processing API for TOOLNEX PDF, image and text tools.",
    version=APP_VERSION,
)

# Public utility API: allow browser requests from the deployed static frontend.
# No cookies or credentialed requests are used.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


def output_file(data: bytes, filename: str, media_type: str):
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename) or "download"
    headers = {"Content-Disposition": f'attachment; filename="{safe_name}"'}
    return StreamingResponse(io.BytesIO(data), media_type=media_type, headers=headers)


async def read_upload(upload: UploadFile) -> bytes:
    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Please select a file.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 15 MB.")
    return data


def validate_pdf(data: bytes) -> PdfReader:
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise HTTPException(status_code=400, detail="Password-protected PDFs are not supported yet.")
        if len(reader.pages) == 0:
            raise HTTPException(status_code=400, detail="The PDF has no pages.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise HTTPException(status_code=413, detail="PDF exceeds the 200-page limit.")
        return reader
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="This file is not a valid PDF.")


def open_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
        return ImageOps.exif_transpose(image)
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(status_code=400, detail="This is not a supported or safe image file.")


@app.get("/")
def root():
    return {"name": "TOOLNEX API", "status": "running", "version": APP_VERSION, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "toolnex-api", "version": APP_VERSION}


@app.get("/api/tools")
def tools_catalog():
    return {"tools": [
        {"id": "pdf-merge", "name": "PDF Merge", "category": "PDF", "endpoint": "/api/pdf/merge"},
        {"id": "pdf-split", "name": "PDF Split", "category": "PDF", "endpoint": "/api/pdf/split"},
        {"id": "pdf-compress", "name": "PDF Compress", "category": "PDF", "endpoint": "/api/pdf/compress"},
        {"id": "image-compress", "name": "Image Compress", "category": "Image", "endpoint": "/api/image/compress"},
        {"id": "image-resize", "name": "Image Resize", "category": "Image", "endpoint": "/api/image/resize"},
        {"id": "image-convert", "name": "Image Convert", "category": "Image", "endpoint": "/api/image/convert"},
        {"id": "word-counter", "name": "Word Counter", "category": "Text", "endpoint": "/api/text/word-count"},
    ]}


@app.post("/api/pdf/merge")
async def pdf_merge(files: Annotated[list[UploadFile], File(description="Select 2 to 10 PDF files")]):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Upload at least 2 PDF files.")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="You can merge up to 10 PDFs at a time.")
    writer = PdfWriter()
    for upload in files:
        reader = validate_pdf(await read_upload(upload))
        for page in reader.pages:
            writer.add_page(page)
    result = io.BytesIO()
    writer.write(result)
    writer.close()
    return output_file(result.getvalue(), "toolnex-merged.pdf", "application/pdf")


@app.post("/api/pdf/split")
async def pdf_split(file: Annotated[UploadFile, File()], start_page: Annotated[int, Form(ge=1)] = 1, end_page: Annotated[int, Form(ge=1)] = 1):
    reader = validate_pdf(await read_upload(file))
    if start_page > end_page or end_page > len(reader.pages):
        raise HTTPException(status_code=400, detail=f"Choose a valid page range from 1 to {len(reader.pages)}.")
    writer = PdfWriter()
    for page_index in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_index])
    result = io.BytesIO()
    writer.write(result)
    writer.close()
    return output_file(result.getvalue(), "toolnex-split.pdf", "application/pdf")


@app.post("/api/pdf/compress")
async def pdf_compress(file: Annotated[UploadFile, File()]):
    data = await read_upload(file)
    validate_pdf(data)
    try:
        document = fitz.open(stream=data, filetype="pdf")
        result = document.tobytes(garbage=4, deflate=True, clean=True)
        document.close()
    except Exception:
        raise HTTPException(status_code=400, detail="The PDF could not be compressed.")
    return output_file(result, "toolnex-compressed.pdf", "application/pdf")


@app.post("/api/image/compress")
async def image_compress(file: Annotated[UploadFile, File()], quality: Annotated[int, Form(ge=20, le=95)] = 75):
    image = open_image(await read_upload(file)).convert("RGB")
    result = io.BytesIO()
    image.save(result, format="JPEG", quality=quality, optimize=True)
    return output_file(result.getvalue(), "toolnex-compressed.jpg", "image/jpeg")


@app.post("/api/image/resize")
async def image_resize(file: Annotated[UploadFile, File()], width: Annotated[int, Form(ge=1, le=6000)], height: Annotated[int, Form(ge=1, le=6000)]):
    if width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(status_code=400, detail="Requested dimensions are too large.")
    image = open_image(await read_upload(file))
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    result = io.BytesIO()
    fmt = "PNG" if image.mode in ("RGBA", "P") else "JPEG"
    if fmt == "JPEG":
        image = image.convert("RGB")
    image.save(result, format=fmt, optimize=True)
    extension = "png" if fmt == "PNG" else "jpg"
    media_type = "image/png" if fmt == "PNG" else "image/jpeg"
    return output_file(result.getvalue(), f"toolnex-resized.{extension}", media_type)


@app.post("/api/image/convert")
async def image_convert(file: Annotated[UploadFile, File()], format: Annotated[str, Form()] = "png"):
    fmt = format.lower()
    if fmt not in {"png", "jpg", "jpeg", "webp"}:
        raise HTTPException(status_code=400, detail="Choose PNG, JPG or WEBP.")
    image = open_image(await read_upload(file))
    result = io.BytesIO()
    if fmt in {"jpg", "jpeg"}:
        image.convert("RGB").save(result, format="JPEG", quality=90, optimize=True)
        return output_file(result.getvalue(), "toolnex-converted.jpg", "image/jpeg")
    if fmt == "webp":
        image.save(result, format="WEBP", quality=90, method=4)
        return output_file(result.getvalue(), "toolnex-converted.webp", "image/webp")
    image.save(result, format="PNG", optimize=True)
    return output_file(result.getvalue(), "toolnex-converted.png", "image/png")


class WordCountRequest(BaseModel):
    text: str = Field(max_length=200_000)


@app.post("/api/text/word-count")
def word_count(payload: WordCountRequest):
    value = payload.text
    return {
        "characters": len(value),
        "characters_without_spaces": len(re.sub(r"\s", "", value)),
        "words": len(re.findall(r"\S+", value)),
        "lines": len(value.splitlines()) if value else 0,
    }
