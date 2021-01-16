import yaml
from numbers import Number
from typing import List, NamedTuple, Optional

from hwmonitoring.config import Kafka


class Task(NamedTuple):
    delay: Number
    max_coroutines: int
    url: str
    patterns: Optional[List[str]]


class Config(NamedTuple):
    producer: Kafka
    tasks: List[Task]


def parse_config_file(filename: str) -> Config:
    with open(filename, 'r') as configfile:
        config = yaml.safe_load(configfile)
        return Config(
            producer=Kafka(**config.get('producer', {})),
            tasks=list([Task(**task) for task in config.get('tasks', {})]))
