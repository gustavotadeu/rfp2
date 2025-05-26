from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import EscopoServico, RFP, User
from auth import get_db, get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/escopos", tags=["escopos"])

class EscopoServicoCreate(BaseModel):
    titulo: str
    descricao: str = None

class EscopoServicoOut(BaseModel):
    id: int
    rfp_id: int
    titulo: str
    descricao: str | None = None
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True

@router.post("/rfp/{rfp_id}", response_model=EscopoServicoOut)
def create_escopo(rfp_id: int, escopo: EscopoServicoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    novo = EscopoServico(rfp_id=rfp_id, titulo=escopo.titulo, descricao=escopo.descricao)
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/rfp/{rfp_id}", response_model=List[EscopoServicoOut])
def list_escopos(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(EscopoServico).filter(EscopoServico.rfp_id == rfp_id).all()

@router.put("/{escopo_id}", response_model=EscopoServicoOut)
def update_escopo(escopo_id: int, escopo: EscopoServicoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(EscopoServico).filter(EscopoServico.id == escopo_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Escopo não encontrado")
    obj.titulo = escopo.titulo
    obj.descricao = escopo.descricao
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{escopo_id}")
def delete_escopo(escopo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    obj = db.query(EscopoServico).filter(EscopoServico.id == escopo_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Escopo não encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}

# Endpoint para sugerir escopo via IA
from openai import OpenAI
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/rfp/{rfp_id}/sugerir", response_model=EscopoServicoCreate)
def sugerir_escopo_ia(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or not rfp.resumo_ia:
        raise HTTPException(status_code=404, detail="RFP não encontrada ou sem resumo IA")
    prompt = f"""
Considerando o seguinte resumo de uma RFP, gere uma sugestão de escopo de serviços (em português, formato Markdown):\n\nResumo:\n{rfp.resumo_ia}\n\nSugira um título objetivo e um texto descritivo para o escopo de serviços.\n\nFormato de resposta:\nTÍTULO: <título>\nDESCRICAO: <descrição detalhada em Markdown>"""
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.3,
    )
    content = response.choices[0].message.content
    # Extrair título e descrição
    titulo = "Sugestão de Escopo"
    descricao = content
    if "TÍTULO:" in content and "DESCRICAO:" in content:
        try:
            titulo = content.split("TÍTULO:")[1].split("DESCRICAO:")[0].strip()
            descricao = content.split("DESCRICAO:")[1].strip()
        except Exception:
            pass
    return EscopoServicoCreate(titulo=titulo, descricao=descricao)
