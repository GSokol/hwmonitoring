from typing import List, NamedTuple


class Match(NamedTuple):
    """ RegExp match """

    pattern: str
    count: int


class ModelV1(NamedTuple):
    """ Metric measure entity """

    timestamp: float
    code: int
    latency: float
    matches: List[Match]
    url: str

    def as_dict(self):
        """ Recurcively move to dict """

        self_dict = self._asdict()
        self_dict['matches'] = list([match._asdict()
                                     for match in self.matches])
        return self_dict
