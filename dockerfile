FROM python:3.12

WORKDIR /app

# Copia todo el directorio de la aplicación al contenedor
COPY . /app/

# Instala las dependencias y limpia la caché en un solo paso
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && sed -i '1794s/^/#/' /usr/local/lib/python3.12/site-packages/youtube_dl/extractor/youtube.py

# Define las variables de entorno
ENV TOKEN_BOT=MTE5Nzc0MTY4MDcyMDM2NzYyNg.G4YCys.pqKscxt9el0fwNYvLlXLhxkGgJoDLAvODzrob8
ENV GOOGLE_API_KEY=AIzaSyDj7z4UKupYIyqh4NhyeCntYlek2n8NZoY

# Comando por defecto al ejecutar el contenedor
CMD ["python", "main.py"]