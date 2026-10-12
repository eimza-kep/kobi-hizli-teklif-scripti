FROM python:3.12-alpine

WORKDIR /app

COPY . /app

RUN chmod -R 755 /app

ENV PORT=8081
EXPOSE 8081

CMD ["python", "server.py"]
