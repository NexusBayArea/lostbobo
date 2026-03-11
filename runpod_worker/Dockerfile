FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel

WORKDIR /app

# Install system dependencies for PDF generation if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

# Pre-fetch the model during build if the library supports it to further reduce cold start
# RUN python -c "from mercury import MercuryModel; MercuryModel()"

CMD ["python", "-u", "handler.py"]
