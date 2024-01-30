# Usa una imagen base de Python
FROM python:3.8

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos necesarios al contenedor
COPY main.py /app/
COPY requirements.txt /app/


#modificar el youtube
# Instala ffmpeg desde el sistema de paquetes del contenedor
RUN apt-get update && apt-get install -y ffmpeg


# Instala las dependencias de Python
RUN pip install -r requirements.txt


#RUN sed -i '1794s/^/#/' /usr/local/lib/python3.12/site-packages/youtube_dl/extractor/youtube.py

# Instala las dependencias y actualiza los paquetes
# Establece la variable de entorno con el token
ENV TOKEN=MTE5Nzc0MTY4MDcyMDM2NzYyNg.GN6p9X._VuHIVT-NqHehmvxpLkPUUEDEFSkXV_gVR-pHk
ENV GOOGLE_API_KEY=AIzaSyDj7z4UKupYIyqh4NhyeCntYlek2n8NZoY

# Comando para ejecutar el bot
CMD ["python", "main.py"]