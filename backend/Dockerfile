FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

COPY . .

CMD ["./wait-for-db.sh"]

