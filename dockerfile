# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY requirements.txt requirements.txt

# Instala las dependencias y actualiza los paquetes
RUN apt-get update && apt-get install -y ffmpeg \
    && pip install -r requirements.txt

# Comando para ejecutar el bot
CMD ["python", "main.py"]