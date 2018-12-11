FROM ubuntu:xenial
MAINTAINER Bluesoft Fire <devops@bluesoft.com.br>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update -qq&& \
    apt-get -y install \
        gcc \
        ipython \
        libz-dev \
        libxml2-dev \
        libxslt1-dev \
        mongodb \
        python2.7 \
        python2.7-dev \
        libyaml-dev \
	libpython2.7-dev \
	python-pip

RUN pip install --upgrade pip==18.0 setuptools wheel

ENV APP_DIR /srv/postmon

RUN mkdir -p $APP_DIR
ADD . $APP_DIR
WORKDIR $APP_DIR

RUN pip install -r requirements.txt
RUN mkdir -p data/db

EXPOSE 9876

ENTRYPOINT mongod \
                --fork \
                --logpath /tmp/mongo.log \
                --dbpath data/db && \
           python PostmonServer.py

