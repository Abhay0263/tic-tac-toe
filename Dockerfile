FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/wait-for-db.sh .
RUN chmod +x wait-for-db.sh

COPY backend/ .

CMD ["./wait-for-db.sh"]
