FROM python:3.11-slim

WORKDIR /app

COPY services/module-runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/module-runtime/ .
COPY services/proto/ services/proto/

EXPOSE 50052

CMD ["python", "-u", "main.py"]
