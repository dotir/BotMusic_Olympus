# Usa una imagen base de Python
FROM python:3.8-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY requirements.txt requirements.txt
COPY music_bot.py music_bot.py

# Instala las dependencias
RUN pip install -r requirements.txt

# Comando para ejecutar el bot
CMD ["python", "music_bot.py"]
