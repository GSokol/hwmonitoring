from typing import NamedTuple

KAFKA_CERT_PASSWORD_KEY = 'KAFKA_CERT_PASSWORD'


class Kafka(NamedTuple):
    cafile: str
    certfile: str
    keyfile: str
    password: str
    bootstrap_servers: str
    topic: str
