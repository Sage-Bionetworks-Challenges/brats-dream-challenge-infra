FROM python:3.8.1-slim-buster

RUN pip install pandas synapseclient nibabel

COPY utils.py /usr/local/bin/.
COPY validate.py /usr/local/bin/.
COPY score.py /usr/local/bin/.
