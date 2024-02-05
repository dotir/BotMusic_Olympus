FROM python:3.12

WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY main.py /app/
COPY requirements.txt /app/

# Instala las dependencias del sistema
RUN apt-get update && apt-get install -y ffmpeg

# Crea y activa el entorno virtual
RUN python -m venv venv
SHELL ["/bin/bash", "-c"]
RUN source venv/bin/activate

# Instala las dependencias de Python dentro del entorno virtual
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Desactiva el entorno virtual para que no quede activado en la imagen final
#RUN deactivate

# Modifica el archivo necesario
RUN sed -i '1794s/^/#/' /usr/local/lib/python3.12/site-packages/youtube_dl/extractor/youtube.py

# Configura las variables de entorno
ENV TOKEN_BOT=MTE5Nzc0MTY4MDcyMDM2NzYyNg.G4YCys.pqKscxt9el0fwNYvLlXLhxkGgJoDLAvODzrob8
ENV GOOGLE_API_KEY=AIzaSyDj7z4UKupYIyqh4NhyeCntYlek2n8NZoY

# Establece el comando de inicio
CMD ["python", "main.py"]
