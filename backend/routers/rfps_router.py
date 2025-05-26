from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from auth import get_db, get_current_user
from models import RFP, User, Vendor, AIProvider, RFPFile, AIPrompt # Added AIPrompt
from routers.ai_providers_router import get_selected_provider
from openai import OpenAI
import os
import uuid
import datetime
import shutil
from pydantic import BaseModel
from docx import Document
from PyPDF2 import PdfReader

# Initialize router for RFP endpoints
router = APIRouter(prefix="/rfps", tags=["RFPs"])

# Helper function to get prompt text by name
def get_prompt_text_by_name(db: Session, name: str) -> str:
    prompt_obj = db.query(AIPrompt).filter(AIPrompt.name == name).first()
    if not prompt_obj:
        raise HTTPException(status_code=500, detail=f"Prompt '{name}' not found in database.")
    return prompt_obj.prompt_text

# --- Request and Response Models ---
class RFPCreate(BaseModel):
    nome: str
    status: str = "Criado"

class RFPUpdate(BaseModel):
    nome: str = None
    status: str = None

class RFPOut(BaseModel):
    id: int
    nome: str
    status: str
    arquivo_url: str | None = None
    resumo_ia: str | None = None
    fabricante_escolhido_id: int | None = None
    analise_vendors: str | None = None
    class Config:
        orm_mode = True

class VendorMatchSave(BaseModel):
    analise: str

class FabricanteEscolhidoUpdate(BaseModel):
    fabricante_escolhido_id: int


class VendorCreate(BaseModel):
    nome: str
    tecnologias: str = ""
    produtos: str = ""
    certificacoes: str = ""
    requisitos_atendidos: str = ""

class VendorOut(BaseModel):
    id: int
    nome: str
    tecnologias: str
    produtos: str
    certificacoes: str
    requisitos_atendidos: str
    class Config:
        orm_mode = True

@router.post("/vendors", response_model=VendorOut)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
    v = Vendor(
        nome=vendor.nome,
        tecnologias=vendor.tecnologias,
        produtos=vendor.produtos,
        certificacoes=vendor.certificacoes,
        requisitos_atendidos=vendor.requisitos_atendidos
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

@router.get("/vendors", response_model=List[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return db.query(Vendor).all()

@router.post("/{rfp_id}/save-vendor-analysis")
def save_vendor_analysis(rfp_id: int, data: VendorMatchSave, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    rfp.analise_vendors = data.analise
    rfp.status = "Analise Vendors"
    db.commit()
    db.refresh(rfp)
    return {"msg": "Análise dos vendors salva com sucesso"}

@router.get("/{rfp_id}/vendors-matching")
def match_vendors_to_rfp(rfp_id: int, db: Session = Depends(get_db), provider: AIProvider = Depends(get_selected_provider)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or not rfp.resumo_ia:
        raise HTTPException(status_code=404, detail="RFP não encontrada ou sem análise IA")

    vendors = db.query(Vendor).all()
    if not vendors:
        return JSONResponse(content=[])

    # Preparar contexto para IA
    vendors_info = "\n".join([
        f"Vendor: {v.nome}\nTecnologias: {v.tecnologias}\nProdutos: {v.produtos}\nCertificacoes: {v.certificacoes}\nRequisitos_Atendidos: {v.requisitos_atendidos}"
        for v in vendors
    ])

    system_prompt_text = get_prompt_text_by_name(db, "vendor_matching_system_role")
    user_prompt_template = get_prompt_text_by_name(db, "vendor_matching_user_prompt")
    
    user_content = user_prompt_template.format(rfp_summary=rfp.resumo_ia, vendors_info=vendors_info)

    # Instantiate client with selected provider
    client = OpenAI(api_key=provider.api_key)
    # Chamada à LLM configurada
    response = client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": system_prompt_text},
            {"role": "user", "content": user_content}
        ],
        max_tokens=4096,
        temperature=0.2
    )
    import json
    # Extrair JSON da resposta
    import re as regex
    ai_content = response.choices[0].message.content
    # Extrai o primeiro bloco JSON da resposta
    json_match = regex.search(r'\[.*\]', ai_content, regex.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            # Enriquecer cada item com vendor_id
            for item in result:
                vendor_obj = next((v for v in vendors if v.nome == item.get("vendor")), None)
                if vendor_obj:
                    item["vendor_id"] = vendor_obj.id
            return JSONResponse(content=result)
        except Exception:
            pass
    return JSONResponse(content={"erro": "Falha ao processar resposta da IA", "raw": ai_content})

@router.post("/{rfp_id}/set-fabricante-escolhido")
def set_fabricante_escolhido(rfp_id: int, data: FabricanteEscolhidoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    rfp.fabricante_escolhido_id = data.fabricante_escolhido_id
    db.commit()
    db.refresh(rfp)
    return {"msg": "Fabricante escolhido atualizado com sucesso"}

def match_vendors_to_rfp(rfp_id: int, db: Session = Depends(get_db)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or not rfp.resumo_ia:
        raise HTTPException(status_code=404, detail="RFP não encontrada ou sem análise IA")

    vendors = db.query(Vendor).all()
    if not vendors:
        return JSONResponse(content=[])

    # Preparar contexto para IA
    vendors_info = "\n".join([
        f"Vendor: {v.nome}\nTecnologias: {v.tecnologias}\nProdutos: {v.produtos}\nCertificacoes: {v.certificacoes}\nRequisitos_Atendidos: {v.requisitos_atendidos}"
        for v in vendors
    ])
    prompt = (
        "Você é um consultor técnico especializado em pré-vendas. Receberá abaixo o resumo de uma RFP e uma lista de vendors/fabricantes com suas características.\n"
        "Avalie, para cada vendor, o nível de aderência aos requisitos da RFP.\n"
        "Para cada vendor, atribua uma pontuação de 0 a 10 e explique resumidamente o motivo da nota, indicando requisitos atendidos e não atendidos.\n"
        "Responda em JSON, com o seguinte formato:\n"
        "[{'vendor': <nome>, 'score': <0-10>, 'motivo': <texto explicativo>}, ...]\n"
        "\nResumo da RFP:\n" + rfp.resumo_ia +
        "\n\nVendors:\n" + vendors_info +
        "\n\nResponda apenas com o JSON solicitado, sem comentários extras."
    )

    # Chamada à OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um consultor técnico de pré-vendas."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.2
    )
    import json
    # Extrair JSON da resposta
    import re as regex
    ai_content = response.choices[0].message.content
    # Extrai o primeiro bloco JSON da resposta
    json_match = regex.search(r'\[.*\]', ai_content, regex.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(0))
            # Enriquecer cada item com vendor_id
            for item in result:
                vendor_obj = next((v for v in vendors if v.nome == item.get("vendor")), None)
                if vendor_obj:
                    item["vendor_id"] = vendor_obj.id
            return JSONResponse(content=result)
        except Exception:
            pass
    return JSONResponse(content={"erro": "Falha ao processar resposta da IA", "raw": ai_content})

@router.get("/", response_model=List[RFPOut])
def list_rfps(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil == 'admin':
        rfps = db.query(RFP).all()
    else:
        rfps = db.query(RFP).filter(RFP.user_id == current_user.id).all()
    return rfps

@router.post("/", response_model=RFPOut)
def create_rfp(rfp: RFPCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_rfp = RFP(nome=rfp.nome, status=rfp.status, user_id=current_user.id)
    db.add(new_rfp)
    db.commit()
    db.refresh(new_rfp)
    return new_rfp

@router.get("/{rfp_id}", response_model=RFPOut)
def get_rfp(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    return rfp

@router.put("/{rfp_id}", response_model=RFPCreate)
def update_rfp(rfp_id: int, rfp_update: RFPUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    if rfp_update.nome:
        rfp.nome = rfp_update.nome
    if rfp_update.status:
        rfp.status = rfp_update.status
    db.commit()
    db.refresh(rfp)
    return rfp

@router.delete("/{rfp_id}")
def delete_rfp(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    if current_user.perfil != 'admin':
        raise HTTPException(status_code=403, detail="Apenas administradores podem remover RFPs")
    db.delete(rfp)
    db.commit()
    return {"ok": True}

# --- NOVOS ENDPOINTS ---
import shutil
import os

class RFPFileOut(BaseModel):
    id: int
    filename: str
    created_at: datetime.datetime
    class Config:
        orm_mode = True

@router.get("/{rfp_id}/files", response_model=List[RFPFileOut])
@router.get("/{rfp_id}/list", response_model=List[RFPFileOut], include_in_schema=False)
def list_rfp_files(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    return rfp.files

@router.post("/{rfp_id}/upload", response_model=RFPFileOut)
@router.post("/{rfp_id}/files", response_model=RFPFileOut)
def upload_rfp_file_item(rfp_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    upload_dir = "uploaded_rfps"
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f"{rfp_id}_{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_name)
    file.file.seek(0)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    new_file = RFPFile(rfp_id=rfp_id, filename=file.filename, filepath=file_path)
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    return new_file

@router.get("/{rfp_id}/files/{file_id}/download", response_class=FileResponse)
@router.get("/{rfp_id}/download", response_class=FileResponse)
def download_rfp_file_item(rfp_id: int, file_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if file_id is None:
        rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
        if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
            raise HTTPException(status_code=404, detail="RFP não encontrada")
        if not rfp.arquivo_url:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado para esta RFP")
        file_path = rfp.arquivo_url
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
        filename = os.path.basename(file_path)
        return FileResponse(path=file_path, filename=filename)
    else:
        file_rec = db.query(RFPFile).filter(RFPFile.id == file_id, RFPFile.rfp_id == rfp_id).first()
        if not file_rec:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        rfp = file_rec.rfp
        if current_user.perfil != 'admin' and rfp.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Permissão negada")
        return FileResponse(path=file_rec.filepath, filename=file_rec.filename)

@router.delete("/{rfp_id}/files/{file_id}")
def delete_rfp_file_item(rfp_id: int, file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    file_rec = db.query(RFPFile).filter(RFPFile.id == file_id, RFPFile.rfp_id == rfp_id).first()
    if not file_rec:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    rfp = file_rec.rfp
    if current_user.perfil != 'admin' and rfp.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permissão negada")
    try:
        os.remove(file_rec.filepath)
    except OSError:
        pass
    db.delete(file_rec)
    db.commit()
    return {"ok": True}

@router.post("/{rfp_id}/analyze")
def analyze_rfp(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), provider: AIProvider = Depends(get_selected_provider)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or (current_user.perfil != 'admin' and rfp.user_id != current_user.id):
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    if not getattr(rfp, 'files', None) or len(rfp.files) == 0:
        raise HTTPException(status_code=400, detail="Nenhum arquivo enviado para esta RFP")
    # Concatenar texto de todos os arquivos
    text = ""
    for file_rec in rfp.files:
        path = file_rec.filepath
        ext = os.path.splitext(path)[1].lower()
        content = ""
        if ext == ".docx":
            doc = Document(path)
            content = "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".pdf":
            reader = PdfReader(path)
            content = "\n".join([page.extract_text() or "" for page in reader.pages])
        else:
            continue
        text += f"\n\nConteúdo do arquivo {file_rec.filename}:\n{content}"
    # Instanciar cliente e chamar LLM para gerar resumo a partir dos múltiplos arquivos
    client = OpenAI(api_key=provider.api_key)

    system_prompt_text = get_prompt_text_by_name(db, "rfp_analysis_system_role")
    user_prompt_template = get_prompt_text_by_name(db, "rfp_analysis_user_prompt")
    
    user_content = user_prompt_template.format(text=text)

    # Chamada à LLM configurada
    response = client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": system_prompt_text},
            {"role": "user", "content": user_content}
        ],
        max_tokens=10000, # Consider making this configurable or part of the prompt settings
        temperature=0.3 # Consider making this configurable
    )
    resumo = response.choices[0].message.content
    # Salvar o resumo IA no banco e atualizar status
    rfp.resumo_ia = resumo
    rfp.status = "Análise IA"
    db.commit()
    db.refresh(rfp)
    return {"resumo": resumo}
