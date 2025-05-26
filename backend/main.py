from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, users_router, rfps_router, vendors_router, bom_router, propostas_router, escopo_servico_router, proposta_tecnica_router, ai_config_router, ai_providers_router, ai_prompts_router # Added ai_prompts_router

from fastapi.staticfiles import StaticFiles
import logging

# Configurar logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Criação da app
app = FastAPI()


# Serve arquivos enviados
app.mount("/uploaded_rfps", StaticFiles(directory="uploaded_rfps", html=False), name="uploaded_rfps")

# Configuração do CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3001",
    "https://rfp.gustavotadeu.com.br",
    "http://rfp.gustavotadeu.com.br"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Middleware para logar origem e rota
@app.middleware("http")
async def log_requests(request: Request, call_next):
    origin = request.headers.get("origin", "ORIGIN NÃO ENVIADO")
    path = request.url.path
    logging.info(f" Requisição de origem: {origin} → {path}")
    response = await call_next(request)
    return response

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(rfps_router.router)
app.include_router(vendors_router.router)
app.include_router(bom_router.router)
app.include_router(propostas_router.router)
app.include_router(escopo_servico_router.router)
app.include_router(proposta_tecnica_router.router)
app.include_router(ai_config_router.router)
app.include_router(ai_providers_router.router)
app.include_router(ai_prompts_router.router) # Included ai_prompts_router

@app.get("/")
async def root():
    return {"message": "RFP Automation API online"}
