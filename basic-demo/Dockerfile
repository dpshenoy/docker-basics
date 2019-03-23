FROM centos:7

RUN yum -y upgrade && yum clean all \
    && yum -y install epel-release \
    && yum -y install python-pip vim jq

RUN pip install Flask

ADD app.py /app/app.py

WORKDIR /app

USER nobody
