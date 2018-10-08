FROM ubuntu:16.04

RUN apt-get -qqy update \
    && apt-get -qqy install software-properties-common build-essential wget curl p7zip-full zlib1g-dev \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get -qqy update \
    && apt-get -qqy install python3.6 python3.6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/
COPY requirements.txt .
COPY docker/build.sh .
COPY kindlegen .

# when building using LCOW on Windows containers executive bit is not set...
RUN chmod a+x build.sh kindlegen

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3.6 get-pip.py \
    && rm get-pip.py \
    && pip3.6 install -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

ENV ARCH_INSTALLS=linux
CMD ["./build.sh", "latest"]
