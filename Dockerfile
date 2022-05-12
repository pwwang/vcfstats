FROM python:slim-buster

RUN pip install -U cython poetry

WORKDIR /vcfstats
COPY . /vcfstats/

RUN poetry config virtualenvs.create false && \
    pip install -U pip && \
    poetry update && \
    poetry install

CMD ["vcfstats"]
