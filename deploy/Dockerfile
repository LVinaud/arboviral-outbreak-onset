# Imagem do aplicativo para qualquer servidor com Docker (VPS, Cloud Run etc.).
# Não é usada pelo Streamlit Community Cloud, que instala o app/requirements.txt
# e o packages.txt sozinho.
#
#   docker build -f deploy/Dockerfile -t arboviral-alerta .
#   docker run -p 8501:8501 arboviral-alerta
#
# Dados e modelos de treino não entram na imagem: o app baixa o que falta do
# repositório de dados no Hugging Face (ver app/lib/dados.py).
FROM python:3.12-slim

# O LightGBM precisa da biblioteca OpenMP do sistema; o curl é do healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/site

COPY --chown=user app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir --user -r app/requirements.txt

COPY --chown=user app/ app/
COPY --chown=user data/master/municipio_mes.parquet data/master/labels.parquet data/master/
COPY --chown=user data/lookup/municipios_sp_estacoes_inmet.xlsx data/lookup/

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "app/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
