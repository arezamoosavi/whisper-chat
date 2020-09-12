FROM bitnami/minideb:buster

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1


RUN apt-get update \
    # dependencies for building Python packages
    && apt-get install -y build-essential \
    && apt-get install -y bash libc-dev libzbar-dev gcc git curl wget vim nano sudo \
    && apt-get install -y ranger caca-utils highlight atool w3m poppler-utils mediainfo \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Install Python3
RUN apt-get update && apt-get install -y software-properties-common
RUN \
    apt-get update && \
    apt-get install -y python3.7 python3.7-dev python3.7-distutils python3-pip python3-virtualenv && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
RUN update-alternatives --set python /usr/bin/python3.7

RUN pip3 install --upgrade pip

COPY ./src/requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

RUN mkdir -p /main
COPY ./src/main /main

COPY ./src/run.sh /run.sh
RUN chmod a+rwx /run.sh
RUN chmod -R a+rwx /main

ENV PORT=80
EXPOSE $PORT
WORKDIR /main
ENTRYPOINT ["/run.sh"]