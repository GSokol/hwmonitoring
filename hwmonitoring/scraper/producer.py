from asyncio import AbstractEventLoop
import json
from typing import NamedTuple

from aiokafka import AIOKafkaProducer
from aiokafka.helpers import create_ssl_context
from logging import Logger


class Producer:
    """ Wrapper around kafka producer """

    _producer = None

    def __init__(
        self,
        loop: AbstractEventLoop,
        cafile: str,
        certfile: str,
        keyfile: str,
        password: str,
        bootstrap_servers: str,
        topic: str,
        logger: Logger,
    ) -> None:
        self._loop = loop
        self._cafile = cafile
        self._certfile = certfile
        self._keyfile = keyfile
        self._password = password
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._logger = logger

    async def start(self) -> None:
        """ Start the producer """

        if self._producer is None:
            self._producer = AIOKafkaProducer(
                loop=self._loop,
                bootstrap_servers=self._bootstrap_servers,
                enable_idempotence=True,
                security_protocol='SSL',
                ssl_context=create_ssl_context(
                    cafile=self._cafile,
                    certfile=self._certfile,
                    keyfile=self._keyfile,
                    password=self._password,
                ),
            )

        await self._producer.start()

    async def publish_probe_results(
        self,
        probe_result: 'Future[NamedTuple]'
    ) -> None:
        """ Publish probe results """

        probe_result_str = json.dumps((await probe_result).as_dict())
        self._logger.debug(
            'Publishing metrics results %s',
            probe_result_str)
        await self._producer.send_and_wait(
            self._topic,
            bytes(probe_result_str, 'utf-8'),
        )
        self._logger.debug('Publishing done')

    async def stop(self) -> None:
        """ Gracefuly stop the producer """

        await self._producer.stop()
        del self._producer
