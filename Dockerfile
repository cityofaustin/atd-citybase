FROM python:3.13-slim
ENV TZ="America/Chicago"
RUN apt-get update
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/America/Chicago /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata
RUN apt-get upgrade -y
COPY ./requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt --break-system-packages
WORKDIR /root/
