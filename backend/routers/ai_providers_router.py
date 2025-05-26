from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import AIProvider, User
from auth import get_db, get_current_user
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/admin/config/providers", tags=["admin_providers"])

class AIProviderIn(BaseModel):
    name: str
    model: str
    api_key: str

class AIProviderOut(AIProviderIn):
    id: int
    is_selected: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

def admin_only(user: User):
    if user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Permissão negada")

def get_selected_provider(db: Session = Depends(get_db)) -> AIProvider:
    prov = db.query(AIProvider).filter(AIProvider.is_selected == True).first()
    if not prov:
        raise HTTPException(status_code=500, detail="Nenhum provedor IA selecionado")
    return prov

@router.get("/", response_model=List[AIProviderOut])
def list_providers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    admin_only(current_user)
    return db.query(AIProvider).all()

@router.post("/", response_model=AIProviderOut)
def create_provider(data: AIProviderIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    admin_only(current_user)
    now = datetime.datetime.utcnow()
    prov = AIProvider(
        name=data.name,
        model=data.model,
        api_key=data.api_key,
        is_selected=False,
        created_at=now,
        updated_at=now
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov

@router.put("/{provider_id}", response_model=AIProviderOut)
def update_provider(provider_id: int, data: AIProviderIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    admin_only(current_user)
    prov = db.query(AIProvider).filter(AIProvider.id == provider_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provedor não encontrado")
    prov.name = data.name
    prov.model = data.model
    prov.api_key = data.api_key
    prov.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(prov)
    return prov

@router.patch("/{provider_id}/select")
def select_provider(provider_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    admin_only(current_user)
    providers = db.query(AIProvider).all()
    for p in providers:
        p.is_selected = (p.id == provider_id)
    db.commit()
    return {"ok": True}
