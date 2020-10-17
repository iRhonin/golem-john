# https://github.com/openwall/john-packages/blob/master/Dockerfile

FROM golemfactory/base:1.8

RUN apt update 

RUN apt install -y \
    build-essential libssl-dev zlib1g-dev yasm libgmp-dev libpcap-dev pkg-config \
    libbz2-dev wget git libusb-1.0-0-dev

RUN useradd -ms /bin/bash user

RUN git clone https://github.com/openwall/john -b bleeding-jumbo --depth 1 /golem/john

WORKDIR /golem/john/src

RUN ./configure
RUN make -j4 

RUN rm *.o && rm -rf ../.git && rm -rf ../run/ztex && rm -rf ztex && \
    apt -y remove --purge build-essential libssl-dev zlib1g-dev yasm libgmp-dev libpcap-dev pkg-config \
        libbz2-dev wget git libusb-1.0-0-dev && \
    apt -y autoremove && \
    apt -y install libgomp1 && \
    apt -y clean && \
    rm -rf /var/lib/apt/lists/*

RUN chown -R user: /golem/

USER user

RUN chmod -R 777 /golem/

VOLUME /golem/work
