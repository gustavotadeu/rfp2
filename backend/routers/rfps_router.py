from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from auth import get_db, get_current_user
from models import RFP, User, Vendor, AIProvider, RFPFile
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
        f"Vendor: {v.nome}\n"#Tecnologias: {v.tecnologias}\nProdutos: {v.produtos}\nCertificacoes: {v.certificacoes}\nRequisitos_Atendidos: {v.requisitos_atendidos}"
        for v in vendors
    ])
    prompt = prompt = (
            "Avalie, para cada vendor, o nível de aderência aos requisitos da RFP. "
            "Para cada vendor, atribua uma pontuação de **0 a 10**, onde:\n"
            "- **0 (zero)**: O vendor é totalmente incompatível com a solução solicitada na RFP (ex: RFP de hardware, vendor que só oferece software ou serviços não relacionados), ou sua descrição **não apresenta nenhum produto/tecnologia relevante** que sequer comece a atender às funcionalidades gerais da RFP.\n"
            "- **1 a 9**: O vendor possui produtos/tecnologias relevantes mencionadas e uma aderência parcial ou total às funcionalidades requeridas, mas com variações na qualidade, profundidade ou completude do atendimento. Uma pontuação mais alta reflete maior e melhor aderência. Avalie a capacidade do produto/tecnologia mencionada no vendor de atender às funcionalidades da RFP, **desconsiderando aspectos de dimensionamento (sizing, como throughput, sessões, interfaces, etc.) nesta etapa**.\n"
            "- **10 (dez)**: O vendor atende de forma excepcional e abrangente a todas as funcionalidades da RFP, sem ressalvas, e as informações fornecidas indicam uma forte compatibilidade funcional com os requisitos detalhados.\n"
            "Explique o motivo da nota de forma concisa mas **altamente detalhada**, indicando as principais **funcionalidades/características atendidas** e, **CRUCIALMENTE, as funcionalidades ou características ESPECÍFICAS que NÃO SÃO ATENDIDAS, SÃO ATENDIDAS PARCIALMENTE, ou ONDE HÁ PONTOS FRACOS/LACUNAS CLARAS na oferta do vendor em relação à RFP.** Não use frases genéricas como 'sem confirmação de compatibilidade total'. Seja direto sobre o que aparentemente não atende ou atende parcialmente, com base nas informações fornecidas.\n"
            "**Não leve em consideração aspectos de dimensionamento (sizing) ao atribuir a nota ou o motivo.**\n"
            "Sua resposta DEVE ser **APENAS** o JSON, sem nenhum outro texto, preâmbulo ou comentário. "
            "Apresente o JSON no seguinte formato:\n"
            "```json\n"
            "[\n"
            "  {'vendor': '<nome_do_vendor>', 'score': <0-10>, 'motivo': '<texto_explicativo>'},\n"
            "  // ... para cada vendor\n"
            "]\n"
            "```\n"
            "\n## Resumo da RFP:\n" + rfp.resumo_ia +
            "\n\n## Vendors:\n" + vendors_info +
            "\n\nLembre-se: Responda APENAS com o JSON. Não inclua nenhum outro texto."
            )

    # Instantiate client with selected provider
    client = OpenAI(api_key=provider.api_key)
    #client = OpenAI(
    #    api_key="AIzaSyAb1jc89LKFKVsm8O6Tw0PfwAtMmpCYF14",
    #    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    #    )
    # Chamada à LLM configurada
    response = client.chat.completions.create(
        model="gpt-4.1",
        #model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": (
                "Você é um consultor técnico especializado em pré-vendas. Sua função é analisar **exclusivamente** o 'Resumo da RFP' e a 'Lista de Vendors' fornecidos. **NÃO invente ou utilize conhecimento externo sobre modelos ou detalhes de produtos específicos não mencionados explicitamente**, mas interprete a **relevância e potencial adequação** de produtos e tecnologias *mencionadas nos vendors* em relação às **funcionalidades e características** dos requisitos da RFP. **Não considere aspectos de dimensionamento (sizing) ou performance ao avaliar a aderência nesta análise.**\n"
                "Seu objetivo é avaliar a aderência de cada vendor aos requisitos da RFP, com foco especial nas **funcionalidades e características** detalhadas na RFP.\n"
                "Atribua uma pontuação de 0 a 10 para cada vendor, seguindo as diretrizes de escala abaixo, e justifique a nota com base **apenas** nas informações da RFP e do vendor. Sua justificativa deve ser minuciosa, detalhando como as funcionalidades são atendidas (ou não). **Para notas de 1 a 9, a justificativa DEVE indicar as funcionalidades ou características ESPECÍFICAS que não são atendidas, são atendidas apenas parcialmente, ou onde há lacunas evidentes na oferta do vendor com base no resumo da RFP.** Não use termos genéricos como 'sem confirmação de compatibilidade total'.\n"
                "**Critérios de Pontuação:**\n"
                "- **0 (zero)**: Incompatibilidade total com o tipo de solução da RFP (ex: RFP de hardware, vendor que só oferece software ou serviços não relacionados), ou sua descrição **não apresenta nenhum produto/tecnologia relevante** que sequer comece a atender às funcionalidades gerais da RFP.\n"
                "- **1 a 9**: O vendor possui produtos/tecnologias relevantes mencionadas e uma aderência parcial ou com lacunas às funcionalidades, ou aderência total com espaço para melhoria na qualidade/profundidade do atendimento das funcionalidades. Pontuações intermediárias (1-9) são esperadas para a maioria dos casos. Quanto mais alta a nota, maior a proximidade com o atendimento completo e de alta qualidade das funcionalidades, **sem considerar o dimensionamento (sizing)**. Avalie se o tipo de solução ou produto do vendor *parece ser capaz de atender* às funcionalidades da RFP, mesmo que esses detalhes não estejam *explicitamente* no perfil do vendor. A justificativa DEVE ser específica sobre as lacunas ou atendimentos parciais.\n"
                "- **10 (dez)**: Atendimento excepcional e abrangente a *todas* as funcionalidades da RFP, sem ressalvas, e as informações fornecidas indicam uma forte e clara compatibilidade com as **funcionalidades detalhadas da RFP**, **ignorando quaisquer aspectos de dimensionamento (sizing)**.\n"
                "Responda estritamente no formato JSON solicitado, sem comentários extras."
            )},
            {"role": "user", "content": prompt}
        ],
        #max_tokens=10000,
        #temperature=0.2
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
    # Chamada à LLM configurada
    response = client.chat.completions.create(
        model=provider.model,
        messages=[
            {"role": "system", "content": (
                "Seu objetivo é interpretar documentos de RFP enviados, extrair **APENAS** as informações mais importantes diretamente do texto fornecido, "
                "identificar riscos ou lacunas, e apresentar a análise de forma organizada, consultiva e clara em Markdown. "
                "Para equipamentos no item 4, quando um modelo específico não for fornecido, você deve extrair e detalhar as **especificações mínimas técnicas** (ex: portas, velocidades, throughput, sessões, features avançadas, etc.) que são cruciais para o sizing e a seleção correta do equipamento. "
                "Use títulos e listas para estruturar o conteúdo. "
                "**NUNCA invente ou infira informações que não estejam explicitamente presentes na RFP.** "
                "Se alguma informação estiver ausente ou não permitir o sizing, aponte claramente como 'Informação não fornecida - recomendar esclarecimento'. "
                "Seja técnico, profissional e objetivo. Responda exclusivamente com base no conteúdo da RFP."
            )},
            {"role": "user", "content": (
                "Analise o seguinte conteúdo de RFP. Para cada item, extraia as informações **diretamente** da RFP (incluindo anexos ou descrições de especificação técnica se fornecidos). "
                "Estruture a resposta em Markdown seguindo **RIGOROSAMENTE** este formato, preenchendo **TODOS** os tópicos. "
                "Se a informação para um tópico não estiver explicitamente presente na RFP, escreva 'Informação não fornecida - recomendar esclarecimento'.\n"
                "\n## 1. Identificação Geral\n"
                "- **Nome do Projeto:** <preencher>\n"
                "- **Cliente:** <preencher>\n"
                "- **Número da RFP (se aplicável):** <preencher>\n"
                "- **Data de Emissão:** <preencher>\n"
                "- **Data de Entrega da Proposta:** <preencher>\n"
                "\n## 2. Objetivo do Projeto\n"
                "- <preencher>\n"
                "\n## 3. Escopo Técnico\n"
                "- **Descrição geral do escopo:** <preencher>\n"
                "- **Tecnologias envolvidas:** <preencher>\n"
                "- **Quantitativos estimados:** <preencher>\n"
                "\n## 4. Equipamentos e Serviços Detalhados\n"
                "Liste os equipamentos e serviços solicitados, preenchendo as tabelas abaixo. "
                "Para o campo 'Modelo/Descrição' de equipamentos, se um modelo específico não for fornecido, detalhe as **especificações técnicas mínimas** extraídas da RFP que são essenciais para o sizing (por exemplo: para firewall: quantidade e modelos de interfaces, throughput esperado, quantidade de VPNs esperadas, sessões simultâneas; para switch: quantidade de portas, velocidades, features avançadas, capacidade de empilhamento, etc.). essas informações devem ser completas porém direta ao ponto, por exemplo interfaces: 1x 10G SFP+ e 1x 1G SFP, throughput: 10Gbps, sessões: 100.000, etc.\n"
                "Se a RFP não contiver informações suficientes para determinar o modelo ou o sizing, indique 'Informação não fornecida - recomendar esclarecimento' na célula correspondente.\n"
                "\n### Equipamentos\n"
                "| Equipamento | Modelo/Descrição | Quantidade | Observações | Especificações Mínimas |\n"
                "|:------------|:------------------|:-----------|:------------|:------------|\n"
                "| <preencher> | <preencher>       | <preencher>| <preencher> |<preencher> |\n"
                "\n### Serviços\n"
                "| Serviço | Descrição resumida | Observações |\n"
                "|:--------|:-------------------|:------------|\n"
                "| <preencher> | <preencher> | <preencher> |\n"
                "\n## 5. Requisitos Obrigatórios\n"
                "- <preencher>\n"
                "\n## 6. Requisitos Desejáveis\n"
                "- <preencher>\n"
                "\n## 7. Critérios de Qualificação\n"
                "- <preencher>\n"
                "\n## 8. Modelo de Precificação\n"
                "- **Forma de precificação exigida:** <preencher>\n"
                "- **Tipo de contrato:** <preencher>\n"
                "\n## 9. Entregáveis Esperados\n"
                "- <preencher>\n"
                "\n## 10. Prazos e Condições\n"
                "- **Prazos de execução:** <preencher>\n"
                "- **Condições comerciais relevantes:** <preencher>\n"
                "\n## 11. Riscos Identificados\n"
                "- <preencher>\n"
                "\n## 12. Perguntas ou Pontos a Esclarecer\n"
                "- <preencher>\n"
                "\n---\n"
                "**Instruções de Formatação e Conteúdo Adicionais:**\n"
                "- Sempre use listas ou tópicos para respostas longas e para os itens 2, 5, 6, 7, 9, 11 e 12.\n"
                "- Use negrito para títulos internos dos tópicos (ex: **Nome do Projeto**).\n"
                "- Separe visualmente os tópicos com linhas em branco para melhor legibilidade.\n"
                "- Respeite o layout Markdown para garantir legibilidade, mesmo para textos extensos.\n"
                f"\n\nConteúdo da RFP:\n{text}"
            )}
        ],
        max_tokens=10000,
        temperature=0.3
    )
# Extrair o resumo da resposta
    resumo = response.choices[0].message.content
# Salvar o resumo IA no banco e atualizar status
    rfp.resumo_ia = resumo
    rfp.status = "Análise IA"
    db.commit()
    db.refresh(rfp)
    return {"resumo": resumo}
