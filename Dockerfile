FROM python:3.8.3-slim-buster

# set working directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/src/app

# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc ffmpeg \
  && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
RUN pip install flask pydub pyyaml ffmpeg ComplexHTTPServer pydantic

# add app
COPY . /usr/src/app
