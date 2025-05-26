from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from models import Proposta, User, RFP
from auth import get_db, get_current_user
from pydantic import BaseModel
import os
import shutil

class PropostaCreate(BaseModel):
    dados_json: Any = None
    arquivo_pdf: Optional[str] = None
    arquivo_docx: Optional[str] = None

class PropostaUpdate(BaseModel):
    dados_json: Any = None
    arquivo_pdf: Optional[str] = None
    arquivo_docx: Optional[str] = None

router = APIRouter(prefix="/propostas", tags=["propostas"])

@router.get("/rfp/{rfp_id}", response_model=List[PropostaCreate])
def list_propostas(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    propostas = db.query(Proposta).filter(Proposta.rfp_id == rfp_id).all()
    return propostas

@router.post("/rfp/{rfp_id}", response_model=PropostaCreate)
def create_proposta(rfp_id: int, proposta: PropostaCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    new_proposta = Proposta(rfp_id=rfp_id, **proposta.dict())
    db.add(new_proposta)
    db.commit()
    db.refresh(new_proposta)
    return new_proposta

@router.get("/item/{proposta_id}", response_model=PropostaCreate)
def get_proposta(proposta_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    return proposta

@router.put("/item/{proposta_id}", response_model=PropostaCreate)
def update_proposta(proposta_id: int, proposta_update: PropostaUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    for field, value in proposta_update.dict(exclude_unset=True).items():
        setattr(proposta, field, value)
    db.commit()
    db.refresh(proposta)
    return proposta

@router.delete("/item/{proposta_id}")
def delete_proposta(proposta_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    db.delete(proposta)
    db.commit()
    return {"ok": True}

@router.post("/item/{proposta_id}/upload_pdf")
def upload_proposta_pdf(proposta_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    upload_dir = "uploaded_propostas"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"proposta_{proposta_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    proposta.arquivo_pdf = file_path
    db.commit()
    db.refresh(proposta)
    return {"msg": "Arquivo PDF enviado com sucesso", "arquivo_pdf": file_path}

@router.post("/item/{proposta_id}/upload_docx")
def upload_proposta_docx(proposta_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")
    upload_dir = "uploaded_propostas"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"proposta_{proposta_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    proposta.arquivo_docx = file_path
    db.commit()
    db.refresh(proposta)
    return {"msg": "Arquivo DOCX enviado com sucesso", "arquivo_docx": file_path}
