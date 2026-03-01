FROM python:3.11-slim

# Instala dependências do sistema para Chrome + undetected-chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements primeiro (cache de layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código
COPY main.py .

# Variáveis de ambiente (não precisam estar aqui, vão no Render)
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
