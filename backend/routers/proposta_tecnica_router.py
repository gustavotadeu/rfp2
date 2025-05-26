from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import RFP, EscopoServico, User, Proposta, AIProvider, Vendor, BoMItem, RFPFile, AIPrompt # Added AIPrompt
from auth import get_db, get_current_user
from routers.ai_providers_router import get_selected_provider
from pydantic import BaseModel
from openai import OpenAI
import os
import io
import uuid
from fastapi.responses import StreamingResponse
from docxtpl import DocxTemplate
import re
import unicodedata
from jinja2 import TemplateSyntaxError
import logging

logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix="/propostas_tecnicas", tags=["propostas_tecnicas"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Helper function to get prompt text by name
def get_prompt_text_by_name(db: Session, name: str) -> str:
    prompt_obj = db.query(AIPrompt).filter(AIPrompt.name == name).first()
    if not prompt_obj:
        raise HTTPException(status_code=500, detail=f"Prompt '{name}' not found in database.")
    return prompt_obj.prompt_text

class PropostaTecnicaSections(BaseModel):
    introducao: str
    metodologia: str
    cronograma: str
    recursos: str
    class Config:
        orm_mode = True

@router.post("/rfp/{rfp_id}/gerar")
def gerar_proposta_tecnica(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), provider: AIProvider = Depends(get_selected_provider)):
    client = OpenAI(api_key=provider.api_key)
    rfp = db.query(RFP).filter(RFP.id == rfp_id).first()
    if not rfp or not rfp.resumo_ia:
        raise HTTPException(status_code=404, detail="RFP não encontrada ou sem resumo IA")
    escopos = db.query(EscopoServico).filter(EscopoServico.rfp_id == rfp_id).all()
    escopos_text = "\n".join([f"- {e.titulo}: {e.descricao or ''}" for e in escopos])
    # Arquivos anexados
    arquivos = db.query(RFPFile).filter(RFPFile.rfp_id == rfp_id).all()
    arquivos_text = "\n".join([f"- {f.filename}" for f in arquivos]) or "Nenhum arquivo anexado"
    # Vendor selecionado
    if rfp.fabricante_escolhido_id:
        vendor = db.query(Vendor).filter(Vendor.id == rfp.fabricante_escolhido_id).first()
        vendor_info = f"Nome: {vendor.nome}\nTecnologias: {vendor.tecnologias}\nProdutos: {vendor.produtos}\nCertificações: {vendor.certificacoes}\nRequisitos Atendidos: {vendor.requisitos_atendidos}"
    else:
        vendor_info = "Nenhum fabricante selecionado"
    # Itens de BoM
    bom_items = db.query(BoMItem).filter(BoMItem.rfp_id == rfp_id).all()
    bom_text = "\n".join([f"- {item.descricao} (modelo: {item.modelo}, part_number: {item.part_number}, quantidade: {item.quantidade})" for item in bom_items]) or "Nenhum BoM gerado"

    user_prompt_template = get_prompt_text_by_name(db, "technical_proposal_user_prompt")
        
    prompt_content = user_prompt_template.format(
        rfp_nome=rfp.nome,
        arquivos_text=arquivos_text,
        rfp_resumo_ia=rfp.resumo_ia,
        vendor_info=vendor_info,
        bom_text=bom_text,
        escopos_text=escopos_text
    )

    response = client.chat.completions.create(
        model=provider.model,
        messages=[{"role": "user", "content": prompt_content}],
        max_tokens=10000, # Consider making this configurable
        temperature=0.3, # Consider making this configurable
    )
    content = response.choices[0].message.content
    # Extrair seções usando headings '###' no início da linha
    parts = re.split(r"^###\s+", content, flags=re.MULTILINE)
    sections = {}
    for part in parts[1:]:  # pular conteudo antes do primeiro ###
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        heading = lines[0].strip()
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        sections[heading] = body
    # Salvar dados
    obj = db.query(Proposta).filter(Proposta.rfp_id == rfp_id).first()
    if obj:
        obj.dados_json = sections
    else:
        obj = Proposta(rfp_id=rfp_id, dados_json=sections)
        db.add(obj)
    db.commit()
    return sections

@router.get("/rfp/{rfp_id}/download")
def download_proposta_tecnica(rfp_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # busca proposta e dados
    obj = db.query(Proposta).filter(Proposta.rfp_id == rfp_id).first()
    if not obj or not obj.dados_json:
        raise HTTPException(status_code=404, detail="Proposta não encontrada. Gere antes via IA.")
    raw_sections = obj.dados_json
    # normaliza chaves para jinja
    def normalize_key(key: str) -> str:
        nk = unicodedata.normalize('NFKD', key)
        nk = nk.encode('ASCII', 'ignore').decode('ASCII')
        return re.sub(r"\W+", "_", nk).strip("_").upper()
    sections = {normalize_key(k): v for k, v in raw_sections.items()}
    logger.debug("Sections normalized for Jinja: %s", list(sections.keys()))
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "proposta_template.docx")
    try:
        tpl = DocxTemplate(template_path)
        # renderiza e salva buffer
        tpl.render(sections)
        logger.debug("Docx rendered successfully")
        buffer = io.BytesIO()
        tpl.save(buffer)
    except Exception as e:
        logger.error("Falha ao gerar docx", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao gerar proposta docx: {e}")
    buffer.seek(0)
    filename = f"proposta_tecnica_rfp_{rfp_id}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
