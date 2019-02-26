FROM python:3-slim

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update && apt-get install -y curl && \
    pip install --no-cache-dir -r requirements.txt

COPY test.py .

CMD ["sh", "-c", "curl -sS ${QUERY_SCRIPT_URL} > query.py && python -u ./test.py"]