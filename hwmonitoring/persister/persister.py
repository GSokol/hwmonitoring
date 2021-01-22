import asyncio
from logging import Logger
from typing import Iterable

from .consumer import Consumer
from .elt import ELT


class Persister:
    """ Subscribes to the topic and stores results to the database """

    _is_working = True

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        elt: ELT,
        consumer: Consumer,
        logger: Logger,
    ) -> None:
        """ """
        self._loop = loop
        self._elt = elt
        self._consumer = consumer
        self._logger = logger

    async def start(self) -> 'Promise[None]':
        await self._consumer.start()
        while self._is_working:
            self._logger.debug('Start new batch processing')
            batch = await self._consumer.fetch_batch()
            if await self._elt.process_batch(batch):
                await self._consumer.commit()
            self._logger.debug('end batch processing')

    def stop(self) -> None:
        self._is_working = False
