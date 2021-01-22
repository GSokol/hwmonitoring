#! /usr/bin/env python3

import asyncio
import logging
import re
import signal
import sys
import time

import argparse
from envparse import env
from yarl import URL

from hwmonitoring.config import KAFKA_CERT_PASSWORD_KEY
from hwmonitoring.scraper.config import parse_config_file
from hwmonitoring.scraper.scraper import Scraper
from hwmonitoring.scraper.producer import Producer
from hwmonitoring.scraper.task import Task


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Config file', required=True)
    parser.add_argument('--debug', help='Use debug mode', action='store_true',
                        default=False)
    args = parser.parse_args()
    config = parse_config_file(args.config)
    kafka_password = env.str(KAFKA_CERT_PASSWORD_KEY,
                             default=config.producer.password)
    logger = logging.getLogger(__name__)
    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    loop = asyncio.get_event_loop()

    scraper = Scraper(
        loop, Producer(
            loop, config.producer.cafile, config.producer.certfile,
            config.producer.keyfile, kafka_password,
            config.producer.bootstrap_servers, config.producer.topic, logger),
        tasks=[Task(
            delay=task.delay, url=URL(task.url),
            patterns=[re.compile(pattern) for pattern in (
                task.patterns or [])],
            max_coroutines=task.max_coroutines,
            logger=logger) for task in config.tasks],
        logger=logger,
    )

    def shutdown():
        logger.info('Shotdown hwmonitoring persister ...')
        scraper.stop()

        asyncio.gather(asyncio.sleep(2))

        logger.info('Stoping event loop ...')
        loop.stop()
        logger.info('Shutdown complete!')

    loop.add_signal_handler(signal.SIGTERM, shutdown)
    loop.add_signal_handler(signal.SIGTERM, shutdown)

    try:
        loop.create_task(scraper.start())
        loop.run_forever()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
