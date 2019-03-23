FROM python:3.7-slim

ADD requirements.txt /app/requirements.txt

RUN pip install -r /app/requirements.txt 

ADD app.py /app/app.py

ADD trained_classifier.pkl /app/trained_classifier.pkl

WORKDIR /app

USER nobody

CMD ["python", "app.py"]
