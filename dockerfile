# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY main.py /app/
COPY requirements.txt /app/


# Instala ffmpeg desde el sistema de paquetes del contenedor
RUN apt-get update && apt-get install -y ffmpeg

# Instala las dependencias de Python
RUN pip install -r requirements.txt
# Instala las dependencias y actualiza los paquetes

# Comando para ejecutar el bot
CMD ["python", "main.py"]