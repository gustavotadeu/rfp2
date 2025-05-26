from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from auth import get_db, get_password_hash, get_current_user
from pydantic import BaseModel

class UserCreate(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
def create_user(user_data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
    user = User(nome=user_data.nome, email=user_data.email, senha_hash=get_password_hash(user_data.senha), perfil=user_data.perfil)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "nome": user.nome, "email": user.email, "perfil": user.perfil}

@router.get("/")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")
    users = db.query(User).all()
    return [{"id": u.id, "nome": u.nome, "email": u.email, "perfil": u.perfil, "ativo": u.ativo} for u in users]

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(user)
    db.commit()
    return {"ok": True}
