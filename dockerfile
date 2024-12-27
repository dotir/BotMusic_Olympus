FROM python:3.12

# Instala las dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY main.py /app/
COPY requirements.txt /app/

# Usa el shell 'bash' para ejecutar los comandos de activación
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Modifica el archivo necesario
RUN sed -i '1794s/^/#/' /usr/local/lib/python3.12/site-packages/youtube_dl/extractor/youtube.py

# Configura las variables de entorno
#descomentar y colocar tu token
#ENV TOKEN_BOT=tutoken
#ENV GOOGLE_API_KEY=tokendegoogle

# Establece el comando de inicio
CMD ["python", "main.py"]
