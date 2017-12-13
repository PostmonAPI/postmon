FROM ubuntu:14.04
MAINTAINER Bluesoft Fire <devops@bluesoft.com.br>

RUN apt-get -y update && \
    apt-get -y --no-install-recommends install \
        gcc \
        ipython \
        libz-dev \
        libxml2-dev \
        libxslt1-dev \
        mongodb \
        python2.7 \
        python2.7-dev \
        libyaml-dev \
        libpython2.7-dev

ENV APP_DIR /srv/postmon

RUN mkdir -p $APP_DIR
ADD . $APP_DIR
WORKDIR $APP_DIR

RUN python get-pip.py

RUN pip install -r requirements.txt
RUN mkdir -p data/db

EXPOSE 9876

ENTRYPOINT mongod \
                --fork \
                --logpath /tmp/mongo.log \
                --dbpath data/db && \
           python PostmonServer.py

