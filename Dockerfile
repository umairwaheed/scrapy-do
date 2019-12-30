FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
RUN pip install pip==19.3.1
WORKDIR /opt/scrapy_do/

RUN apt install curl
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt install -y nodejs

COPY requirements-dev.txt requirements-dev.txt
RUN pip install -r requirements-dev.txt
