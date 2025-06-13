FROM python:3.9-slim-buster

COPY entrypoint.sh /entrypoint.sh
COPY s3-bucket-usage-exporter.py /s3-bucket-usage-exporter.py
COPY requirements.txt /requirements.txt

RUN chmod +x /entrypoint.sh
RUN chmod +x /s3-bucket-usage-exporter.py

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -L https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/bin/mc \
    && chmod +x /usr/bin/mc 

RUN pip install --no-cache-dir -r requirements.txt
RUN rm /requirements.txt

ENTRYPOINT [ "/entrypoint.sh" ]
