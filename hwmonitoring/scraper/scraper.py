import aiohttp
import asyncio
from logging import Logger
from typing import Sequence

from .task import Task
from .producer import Producer


class Scraper:
    """ Evaluates HTTP probes, process metrics and publish it to Kafka """

    _running = True
    _session = None
    _running_tasks = {}

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        producer: Producer,
        tasks: Sequence[Task],
        logger: Logger
    ) -> None:
        """ Simple store demendencies """

        self._loop = loop
        self._producer = producer
        self._tasks = tasks
        self._logger = logger

    async def start(self):
        """ Add tasks to event loop """

        await self._producer.start()
        self._logger.debug('Producer has started')
        self._session = await aiohttp.ClientSession(
            loop=self._loop,
            headers={'User-Agent': 'hwmonitoring'},
        ).__aenter__()
        for task in self._tasks:
            self._loop.create_task(self._periodic(task))

    def stop(self) -> None:
        """ Gracefull shotdown """

        self._running = False
        if self._session is not None:
            asyncio.gather(self._session.close())

    async def _periodic(self, task: Task):
        """ Run the probe """

        self._logger.debug('Run periodic "%s"', task.url)
        while self._running:
            while self._running_tasks.get(task.url, 0) > task.max_coroutines:
                await asyncio.sleep(task.delay)
            self._running_tasks[task.url] = \
                self._running_tasks.get(task.url, 0) + 1
            probe_result = self._loop.create_task(
                task.exec_probes(self._session, self._running_tasks))
            self._loop.create_task(
                self._producer.publish_probe_results(probe_result)
            )
            await asyncio.sleep(task.delay)
        self._logger.debug('End periodic "%s"', task.url)
