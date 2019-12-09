FROM python:3.7-alpine

RUN mkdir /service
COPY main.py /service

RUN pip install 'Flask' 'gunicorn' \
  && rm -r /root/.cache

WORKDIR /service

CMD ["gunicorn", "-w", "3", "main:app"]
