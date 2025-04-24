FROM python:3.9.2-buster as base
ENV PYTHONUNBUFFERED 1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    wget
WORKDIR /code
COPY . /code/
RUN sed -i 's/\r//' /code/wait-for-it.sh && chmod +x /code/wait-for-it.sh

RUN pip install --upgrade pip

EXPOSE 8000

RUN pip install -r ./requirements.txt --use-deprecated=legacy-resolver
