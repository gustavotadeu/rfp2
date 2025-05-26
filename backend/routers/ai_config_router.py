from fastapi import APIRouter, Depends, HTTPException, FastAPI, Response
from sqlalchemy.orm import Session
from models import AIConfig, User
from auth import get_db, get_current_user
from pydantic import BaseModel
import datetime

router = APIRouter(prefix="/admin/config", tags=["admin_config"])

class AIConfigIn(BaseModel):
    provider: str
    model: str

class AIConfigOut(AIConfigIn):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True

@router.get("/ai", response_model=AIConfigOut)
def get_ai_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Permissão negada")
    cfg = db.query(AIConfig).first()
    if not cfg:
        now = datetime.datetime.utcnow()
        # retorna config vazia para front-end não falhar
        return {"id": 0, "provider": "", "model": "", "created_at": now, "updated_at": now}
    return cfg

@router.post("/ai", response_model=AIConfigOut)
def set_ai_config(data: AIConfigIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Permissão negada")
    cfg = db.query(AIConfig).first()
    now = datetime.datetime.utcnow()
    if cfg:
        cfg.provider = data.provider
        cfg.model = data.model
        cfg.updated_at = now
    else:
        cfg = AIConfig(provider=data.provider, model=data.model, created_at=now, updated_at=now)
        db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg
