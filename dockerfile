FROM python:3.12
WORKDIR /app
COPY main.py /app/
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y ffmpeg
# Instala las dependencias de Python
RUN pip install -r requirements.txt
CMD ["python", "main.py"]