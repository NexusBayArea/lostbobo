FROM locustio/locust:2.32.0

# Install SimHPC dependencies for realistic client behavior
COPY requirements.txt /mnt/locust/
RUN pip install -r /mnt/locust/requirements.txt

WORKDIR /mnt/locust
COPY locustfile.py .
COPY . /app
