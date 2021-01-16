""" Here all metrics are stored """

from contextlib import AbstractContextManager
from numbers import Number
from re import Pattern
import time
from types import TracebackType
from typing import Callable, Optional, Type


class AbstrctMetrics(AbstractContextManager):
    """ Abstract metric """

    _value = None

    def get_value(self) -> Number:
        """ Returns the metrics value """

        if self._value is None:
            raise ValueError('No mesurement was done')
        return self._value


class TimeMetrics(AbstrctMetrics):
    """ Latency metric """

    _start = None

    def __enter__(self) -> 'TimeMetrics':
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._value = time.perf_counter() - self._start


class StatusCodeMetrics(AbstrctMetrics):
    """ Status code metrics """

    def __enter__(self) -> Callable[[int], None]:
        return self._set_code

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        pass

    def _set_code(self, code: int) -> None:
        self._value = code


class RegexpMetrics(AbstrctMetrics):
    """ Count number of matches """

    _response_body = None

    def __init__(self, pattern: Pattern) -> None:
        self.pattern = pattern

    def __enter__(self) -> Callable[[str], None]:
        return self._set_response_body

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._response_body is not None:
            self._value = len(self.pattern.findall(self._response_body))

    def _set_response_body(self, response_body: str) -> None:
        self._response_body = response_body
