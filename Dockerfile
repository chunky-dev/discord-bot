# syntax=docker/dockerfile:1

FROM python:3.10.3-slim-bullseye
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./src/ .
COPY ./config.ini .
ENTRYPOINT ["python3", "main.py"]
