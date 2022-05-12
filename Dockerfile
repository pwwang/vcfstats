FROM python:slim-buster

RUN pip install -U cython poetry

WORKDIR /vcfstats
COPY . /vcfstats/

# Install native libraries, required for numpy
RUN apk --no-cache add musl-dev linux-headers g++

RUN poetry config virtualenvs.create false && \
    pip install -U pip && \
    poetry update && \
    poetry install

CMD ["vcfstats"]
