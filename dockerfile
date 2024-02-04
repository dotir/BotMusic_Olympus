FROM python:3.12
WORKDIR /app
COPY main.py /app/
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y ffmpeg
# Instala las dependencias de Python
RUN pip install -r requirements.txt

ENV TOKEN_BOT=MTE5Nzc0MTY4MDcyMDM2NzYyNg.G4YCys.pqKscxt9el0fwNYvLlXLhxkGgJoDLAvODzrob8
#ENV GOOGLE_API_KEY=AIzaSyDj7z4UKupYIyqh4NhyeCntYlek2n8NZoY

CMD ["python", "main.py"]