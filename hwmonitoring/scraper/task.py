""" Http probe task """

import aiohttp
from contextlib import ExitStack
from logging import Logger
from numbers import Number
from re import Pattern
from time import time
from typing import Optional, Sequence
from yarl import URL

from hwmonitoring.model import Match, ModelV1
from .metrics import RegexpMetrics, StatusCodeMetrics, TimeMetrics


class Task:
    """ Task for http probe """

    def __init__(
        self,
        delay: Number,
        url: URL,
        logger: Logger,
        max_coroutines: int,
        patterns: Optional[Sequence[Pattern]] = None,
    ) -> None:
        self.delay = delay
        self.url = url
        self._patterns = patterns or []
        self._logger = logger
        self.max_coroutines = max_coroutines

    async def exec_probes(self, session: aiohttp.ClientSession,
                          counter: dict):
        """ Execute http probe and count metrics
            exec_probes(session: aiohttp.ClientSession) -> Future[NamedTuple]

            Named tuple contains timestamp, url, and list of metrics.
        """

        self._logger.debug('Start exec probe %s', self.url)
        regexp_metrics = [RegexpMetrics(pattern) for pattern in self._patterns]
        status_code_metrics = StatusCodeMetrics()
        time_metrics = TimeMetrics()
        timestamp = time()
        with ExitStack() as stack:
            pattern_metrics = [stack.enter_context(
                metric) for metric in regexp_metrics]
            body = None
            with status_code_metrics as set_status_code:
                with time_metrics:
                    async with session.get(self.url) as response:
                        set_status_code(response.status)
                        body = await response.text()
            for pattern_metric in pattern_metrics:
                pattern_metric(body)

        self._logger.debug('Publishing results (latency: %f)',
                           time_metrics.get_value())

        counter[self.url] -= 1
        return ModelV1(
            timestamp=timestamp,
            url=self.url.human_repr(),
            latency=time_metrics.get_value(),
            code=status_code_metrics.get_value(),
            matches=list([Match(
                pattern=regexp_metric.pattern.pattern,
                count=regexp_metric.get_value(),
            ) for regexp_metric in regexp_metrics]),
        )
