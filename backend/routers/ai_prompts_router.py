from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models import AIPrompt, User # Adjusted import path
from ..auth import get_db, get_current_user # Adjusted import path

# Pydantic Schemas
class AIPromptBase(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str

class AIPromptCreate(AIPromptBase):
    pass

class AIPromptUpdate(BaseModel): # All fields optional for partial updates
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_text: Optional[str] = None

class AIPromptOut(AIPromptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/admin/config/prompts",
    tags=["admin_prompts"]
)

# Admin check dependency
def admin_only(current_user: User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Permissão negada. Acesso restrito a administradores.")

# Endpoints
@router.post("/", response_model=AIPromptOut)
def create_ai_prompt(
    prompt_data: AIPromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # For admin_only check via Depends
):
    admin_only(current_user) # Perform admin check

    db_prompt_by_name = db.query(AIPrompt).filter(AIPrompt.name == prompt_data.name).first()
    if db_prompt_by_name:
        raise HTTPException(status_code=400, detail=f"Um prompt com o nome '{prompt_data.name}' já existe.")

    new_prompt = AIPrompt(
        name=prompt_data.name,
        description=prompt_data.description,
        prompt_text=prompt_data.prompt_text,
        # created_at and updated_at are handled by server_default
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt

@router.get("/", response_model=List[AIPromptOut])
def list_ai_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # For admin_only check
):
    admin_only(current_user) # Perform admin check
    prompts = db.query(AIPrompt).all()
    return prompts

@router.get("/{prompt_id}", response_model=AIPromptOut)
def get_ai_prompt_by_id(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # For admin_only check
):
    admin_only(current_user) # Perform admin check
    prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt com ID {prompt_id} não encontrado.")
    return prompt

@router.get("/by_name/{prompt_name}", response_model=AIPromptOut)
def get_ai_prompt_by_name( # No admin check for this specific endpoint
    prompt_name: str,
    db: Session = Depends(get_db)
):
    prompt = db.query(AIPrompt).filter(AIPrompt.name == prompt_name).first()
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt com nome '{prompt_name}' não encontrado.")
    return prompt

@router.put("/{prompt_id}", response_model=AIPromptOut)
def update_ai_prompt(
    prompt_id: int,
    prompt_data: AIPromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # For admin_only check
):
    admin_only(current_user) # Perform admin check

    db_prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail=f"Prompt com ID {prompt_id} não encontrado.")

    if prompt_data.name and prompt_data.name != db_prompt.name:
        existing_prompt_with_name = db.query(AIPrompt).filter(AIPrompt.name == prompt_data.name).first()
        if existing_prompt_with_name and existing_prompt_with_name.id != prompt_id:
            raise HTTPException(status_code=400, detail=f"Um prompt com o nome '{prompt_data.name}' já existe.")
    
    update_data = prompt_data.model_dump(exclude_unset=True) # Use model_dump for Pydantic v2+
    for key, value in update_data.items():
        setattr(db_prompt, key, value)
    
    db_prompt.updated_at = datetime.utcnow() # Manually update updated_at

    db.commit()
    db.refresh(db_prompt)
    return db_prompt

@router.delete("/{prompt_id}", response_model=dict)
def delete_ai_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # For admin_only check
):
    admin_only(current_user) # Perform admin check

    db_prompt = db.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    if not db_prompt:
        raise HTTPException(status_code=404, detail=f"Prompt com ID {prompt_id} não encontrado.")

    db.delete(db_prompt)
    db.commit()
    return {"ok": True, "detail": "Prompt excluído com sucesso."}
