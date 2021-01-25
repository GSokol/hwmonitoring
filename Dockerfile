FROM python:3.9-alpine as builder

RUN apk add build-base
RUN pip install --upgrade setuptools wheel

ADD . /app

WORKDIR /app

RUN pip wheel -e ./ -w dist

FROM python:3.9-alpine

RUN mkdir /tmp/hwmonitoring

COPY --from=builder /app/dist/*.whl /tmp/hwmonitoring/

RUN pip install /tmp/hwmonitoring/*.whl
