from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models import BoMItem, User, RFP, Vendor
from auth import get_db, get_current_user
from pydantic import BaseModel
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client2 = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

class BoMItemCreate(BaseModel):
    descricao: str
    modelo: str
    part_number: str
    quantidade: int

class BoMItemUpdate(BaseModel):
    descricao: str = None
    modelo: str = None
    part_number: str = None
    quantidade: int = None

router = APIRouter(prefix="/bom", tags=["bom"])

@router.get("/rfp/{rfp_id}", response_model=List[BoMItemCreate])
def list_bom_items(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    bom_items = db.query(BoMItem).filter(BoMItem.rfp_id == rfp_id).all()
    return bom_items

@router.post("/rfp/{rfp_id}", response_model=BoMItemCreate)
def create_bom_item(rfp_id: int, item: BoMItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP não encontrada")
    new_item = BoMItem(rfp_id=rfp_id, **item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.get("/item/{item_id}", response_model=BoMItemCreate)
def get_bom_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(BoMItem).filter(BoMItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de BoM não encontrado")
    return item

@router.put("/item/{item_id}", response_model=BoMItemCreate)
def update_bom_item(item_id: int, item_update: BoMItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(BoMItem).filter(BoMItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de BoM não encontrado")
    for field, value in item_update.dict(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/item/{item_id}")
def delete_bom_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(BoMItem).filter(BoMItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item de BoM não encontrado")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/rfp/{rfp_id}/generate", response_model=List[BoMItemCreate])
def generate_bom_ia(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or not rfp.resumo_ia or not rfp.fabricante_escolhido_id:
        raise HTTPException(status_code=400, detail="RFP precisa de resumo da IA e fabricante selecionado")
    fabricante = db.query(Vendor).filter(Vendor.id == rfp.fabricante_escolhido_id).first()
    if not fabricante:
        raise HTTPException(status_code=404, detail="Fabricante não encontrado")

    prompt = f"""
Com base nos requisitos abaixo e nas informações do fabricante, por favor, me forneça uma recomendação de sizing de equipamentos detalhada.

Resumo dos Requisitos do Projeto:
{rfp.resumo_ia}

Fabricante Selecionado: {fabricante.nome}


Formato de Resposta JSON:
[

{ '{' }"descricao": <descrição do partnumber resumida, maximo de 30 caracteres>, "modelo": < modelo do produto selecionado >, "part_number": <partnumber real do produto>, "quantidade": < quantidade >{ '}' },

...

]
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": ("Você é um Engenheiro de Soluções Sênior, especialista em dimensionamento (sizing) de hardware e software para projetos de tecnologia. Sua tarefa é analisar os requisitos de um projeto e as especificações de um fabricante para recomendar o equipamento ideal.\n"
            "\n"
            "Suas diretrizes são:\n"
            "1.  **Priorize o Dimensionamento Adequado:** O equipamento recomendado deve atender ou superar as especificações dos requisitos, garantindo que não seja subdimensionado.\n"
            "2.  **Otimização de Custo-Benefício:** Evite equipamentos excessivamente superdimensionados que possam encarecer o projeto desnecessariamente. o Equipamento deve ser o menor possível que atenda as especificações.\n"
            "3.  **Componentes Abrangentes:** Adicione os acessórios, licenciamento, suporte e garantia do fabricante conforme especificação.\n"
            "4.  **Consistência do Suporte/Garantia:** O nível de suporte e garantia deve ser compatível com os part numbers dos itens de hardware e licenciamento recomendados.\n"
            "5.  **Autenticidade:** Não invente part numbers, modelos de equipamentos ou licenças. Use apenas informações que possam ser inferidas dos dados fornecidos ou que sejam de conhecimento comum de produtos do fabricante. Se não tiver certeza, indique uma recomendação genérica ou um placeholder claro.\n"
            "6.  **Formato de Saída:** Responda APENAS com um objeto JSON.\n"
        )},
        {"role": "user", "content": prompt}],
        max_tokens=15000,
        temperature=0.2
    )

    import json, re
    content = response.choices[0].message.content
    # Extrair JSON da resposta
    json_match = re.search(r'\[.*\]', content, re.DOTALL)
    if not json_match:
        raise HTTPException(status_code=500, detail="Resposta da IA não contém JSON válido")
    try:
        items = json.loads(json_match.group(0))
    except Exception:
        raise HTTPException(status_code=500, detail="Falha ao processar JSON gerado pela IA")
    # Limpar BoM antigo
    db.query(BoMItem).filter(BoMItem.rfp_id == rfp_id).delete()
    # Criar novos itens
    result = []
    for item in items:
        new_item = BoMItem(
            rfp_id=rfp_id,
            descricao=item.get("descricao", ""),
            modelo=item.get("modelo", ""),
            part_number=item.get("part_number", ""),
            quantidade=item.get("quantidade", 1)
        )
        db.add(new_item)
        db.flush()
        result.append(BoMItemCreate(
            descricao=new_item.descricao,
            modelo=new_item.modelo,
            part_number=new_item.part_number,
            quantidade=new_item.quantidade
        ))
    db.commit()
    return result
