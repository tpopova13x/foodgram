FROM python:3.11

WORKDIR /app

RUN pip install gunicorn==20.1.0
COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]