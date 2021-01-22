import aiohttp
import asyncio
import logging
import re
from aioresponses import aioresponses
from yarl import URL

from hwmonitoring.scraper.task import Task

def test_task_probe():
    counter = {'https://www.google.com/': 1}
    loop = asyncio.get_event_loop()
    session = aiohttp.ClientSession()
    with aioresponses() as mocked:
        mocked.get('https://www.google.com/', status=200, body='Lalala')

        target = Task(1, URL('https://www.google.com/'), logging.getLogger(), 10,
                      (re.compile('[Ll]a'), re.compile('ol'),))

        metrics = loop.run_until_complete(target.exec_probes(session, counter))

        assert counter['https://www.google.com/'] == 0
        assert metrics.code == 200
        assert metrics.latency > 0
        assert metrics.url == 'https://www.google.com/'
        assert len(metrics.matches) == 2
        for match in metrics.matches:
            if match.pattern == '[Ll]a':
                assert match.count == 3
            elif match.pattern == 'ol':
                assert match.count == 0
            else:
                assert False, "Only patterns '[Ll]a' and 'ol' should appear"
