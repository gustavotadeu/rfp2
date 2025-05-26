from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, nullable=False)  # 'admin' ou 'editor'
    ativo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    tecnologias = Column(Text, nullable=True)
    produtos = Column(Text, nullable=True)
    certificacoes = Column(Text, nullable=True)
    requisitos_atendidos = Column(Text, nullable=True)

from sqlalchemy import ForeignKey

class RFP(Base):
    __tablename__ = 'rfps'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    status = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    vendor_id = Column(Integer, ForeignKey('vendors.id'))
    arquivo_url = Column(String)
    resumo_ia = Column(Text, nullable=True)
    fabricante_escolhido_id = Column(Integer, ForeignKey('vendors.id'), nullable=True)
    analise_vendors = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    propostas = relationship('Proposta', back_populates='rfp')
    files = relationship('RFPFile', back_populates='rfp', cascade='all, delete-orphan')

class BoMItem(Base):
    __tablename__ = 'bom_items'
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey('rfps.id'))
    descricao = Column(String)
    modelo = Column(String)
    part_number = Column(String)
    quantidade = Column(Integer)

class Proposta(Base):
    __tablename__ = 'propostas'
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey('rfps.id'), nullable=False)
    dados_json = Column(JSON, nullable=True)
    arquivo_pdf = Column(String(255), nullable=True)
    arquivo_docx = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    rfp = relationship('RFP', back_populates='propostas')

class EscopoServico(Base):
    __tablename__ = 'escopo_servico'
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey('rfps.id'), nullable=False)
    titulo = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class RFPFile(Base):
    __tablename__ = 'rfp_files'
    id = Column(Integer, primary_key=True, index=True)
    rfp_id = Column(Integer, ForeignKey('rfps.id', ondelete='CASCADE'))
    filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    rfp = relationship('RFP', back_populates='files')

class AIProvider(Base):
    __tablename__ = 'ai_providers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    api_key = Column(String(255), nullable=False)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AIPrompt(Base):
    __tablename__ = 'ai_prompts'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AIConfig(Base):
    __tablename__ = 'ai_config'
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
