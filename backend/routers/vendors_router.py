from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models import Vendor, User
from auth import get_db, get_current_user
from pydantic import BaseModel

class VendorCreate(BaseModel):
    nome: str
    tecnologias: str = None
    produtos: str = None
    certificacoes: str = None
    requisitos_atendidos: str = None

class VendorUpdate(BaseModel):
    nome: str = None
    tecnologias: str = None
    produtos: str = None
    certificacoes: str = None
    requisitos_atendidos: str = None

from typing import Optional

class VendorOut(BaseModel):
    id: int
    nome: str
    tecnologias: Optional[str] = None
    produtos: Optional[str] = None
    certificacoes: Optional[str] = None
    requisitos_atendidos: Optional[str] = None
    class Config:
        orm_mode = True

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("/", response_model=List[VendorOut])
def list_vendors(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendors = db.query(Vendor).all()
    return vendors

@router.post("/", response_model=VendorOut)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Excluir campos não mapeados no modelo (contato, observacoes)
    payload = vendor.dict(exclude_unset=True, exclude={'contato', 'observacoes'})
    new_vendor = Vendor(**payload)
    db.add(new_vendor)
    db.commit()
    db.refresh(new_vendor)
    return new_vendor

@router.get("/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return vendor

@router.put("/{vendor_id}", response_model=VendorOut)
def update_vendor(vendor_id: int, vendor_update: VendorUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    # Excluir campos não mapeados no modelo
    for field, value in vendor_update.dict(exclude_unset=True, exclude={'contato', 'observacoes'}).items():
        setattr(vendor, field, value)
    db.commit()
    db.refresh(vendor)
    return vendor

@router.delete("/{vendor_id}")
def delete_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    db.delete(vendor)
    db.commit()
    return {"ok": True}
