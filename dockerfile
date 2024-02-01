FROM python:3.12
WORKDIR /app
COPY main.py /app/
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y ffmpeg
# Instala las dependencias de Python
RUN pip install -r requirements.txt
#RUN sed -i '1794s/^/#/' /usr/local/lib/python3.12/site-packages/youtube_dl/extractor/youtube.py

ENV TOKEN=MTE5Nzc0MTY4MDcyMDM2NzYyNg.GN6p9X._VuHIVT-NqHehmvxpLkPUUEDEFSkXV_gVR-pHk
ENV GOOGLE_API_KEY=AIzaSyDj7z4UKupYIyqh4NhyeCntYlek2n8NZoY


CMD ["python", "main.py"]