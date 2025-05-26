FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000

# Adiciona labels para Traefik permitir CORS
LABEL traefik.http.middlewares.cors.headers.accesscontrolalloworigin="*"
LABEL traefik.http.middlewares.cors.headers.accesscontrolallowmethods="GET,OPTIONS,POST,PUT,DELETE"
LABEL traefik.http.middlewares.cors.headers.accesscontrolallowheaders="*"
LABEL traefik.http.routers.rfp_backend.middlewares="cors"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
