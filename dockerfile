# Usa una imagen base de Python
FROM python:3.10

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY requirements.txt requirements.txt
COPY music_bot.py music_bot.py

# Instala las dependencias
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install -r requirements.txt
RUN pip install --force-reinstall https://github.com/yt-dlp/yt-dlp/archive/master.tar.gz

# Comando para ejecutar el bot
CMD ["python", "music_bot.py"]
