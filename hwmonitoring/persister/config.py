from typing import NamedTuple, Optional

import yaml

from hwmonitoring.config import Kafka

class ELT(NamedTuple):
    dsn: Optional[str]
    schema: str

class Consumer(NamedTuple):
    kafka: Kafka
    consumer_group: str
    timeout_ms: int

class Config(NamedTuple):
    consumer: Consumer
    elt: ELT

def parse_config_file(filename: str) -> Config:
    with open(filename, 'r') as configFile:
        config = yaml.safe_load(configFile)
        consumer =  config.get('consumer', {})
        elt = config.get('elt', {})
        return Config(
            consumer=Consumer(
                kafka=Kafka(**consumer.get('kafka', {})),
                consumer_group=consumer['consumer_group'],
                timeout_ms=consumer['timeout_ms']),
            elt=ELT(**config.get('elt', {})))
