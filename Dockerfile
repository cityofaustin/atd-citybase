FROM ubuntu:22.04
ENV TZ="America/Chicago"
RUN apt-get update
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/America/Chicago /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
RUN apt-get upgrade -y
RUN apt-get install -y vim magic-wormhole aptitude python3-pip docker.io
COPY ./requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt
WORKDIR /root/
