FROM python:3.7-alpine

RUN mkdir /service
COPY main.py /service

RUN pip install --no-cache-dir 'Flask' 'gunicorn' 'requests-gcp'

WORKDIR /service

CMD ["gunicorn", "main:app"]
