FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

COPY . .

CMD ["python", "app.py"]
