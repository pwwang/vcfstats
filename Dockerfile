FROM debian:buster-slim

RUN apt-get update \
 && apt-get install --yes --no-install-recommends r-cran-ggplot2 \
            build-essential libz-dev libcurl4-openssl-dev libssl-dev \
            libbz2-dev liblzma-dev \
            python3 python3-wheel python3-dev python3-setuptools python3-pip \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN R -e 'install.packages("ggrepel")'
RUN python3 -m pip install poetry

WORKDIR /vcfstats
COPY . /vcfstats/

RUN poetry config virtualenvs.create false \
 && poetry install
