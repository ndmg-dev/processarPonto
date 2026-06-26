import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from app.models.schemas import UploadResult
from app.services.pdf_reader import extract_pages_text
from app.services.parser import parse_pdf_pages
from app.services.report_generator import generate_pdf_report

app = FastAPI(title="Processamento de Ponto Eletrônico")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desenvolvimento
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "app/storage/uploads"
REPORT_DIR = "app/storage/reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/upload", response_model=UploadResult)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")
        
    upload_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{upload_id}_{file.filename}")
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    try:
        pages_text = extract_pages_text(file_path)
        employees = parse_pdf_pages(pages_text)
        
        result = {
            "upload_id": upload_id,
            "file_name": file.filename,
            "total_employees": len(employees),
            "employees": employees
        }
        
        # Salva resultado em JSON para leitura posterior
        json_path = os.path.join(UPLOAD_DIR, f"{upload_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/uploads/{upload_id}", response_model=UploadResult)
def get_upload_result(upload_id: str):
    json_path = os.path.join(UPLOAD_DIR, f"{upload_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    return data

@app.post("/api/uploads/{upload_id}/report")
def generate_report(upload_id: str):
    json_path = os.path.join(UPLOAD_DIR, f"{upload_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Processamento não encontrado.")
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    report_filename = f"relatorio_{upload_id}.pdf"
    report_path = os.path.join(REPORT_DIR, report_filename)
    
    generate_pdf_report(data, report_path)
    
    return {"report_url": f"/api/reports/{report_filename}"}

@app.get("/api/reports/{file_name}")
def download_report(file_name: str):
    report_path = os.path.join(REPORT_DIR, file_name)
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
        
    return FileResponse(report_path, media_type="application/pdf", filename=file_name)
