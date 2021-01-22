#! /usr/bin/env python3

import asyncio
import logging
import signal
import sys
import time

import argparse
from envparse import env

from hwmonitoring.config import KAFKA_CERT_PASSWORD_KEY
from hwmonitoring.persister.config import parse_config_file
from hwmonitoring.persister.consumer import Consumer
from hwmonitoring.persister.elt import ELT
from hwmonitoring.persister.persister import Persister


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Config file', required=True)
    parser.add_argument('--debug', help='Use debug mode', default=False)
    args = parser.parse_args()
    config = parse_config_file(args.config)
    dsn = env.str('DSN', default=config.elt.dsn)
    kafka_password = env.str(KAFKA_CERT_PASSWORD_KEY,
                             default=config.consumer.kafka.password)
    logger = logging.getLogger(__name__)
    if (args.debug):
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    loop = asyncio.get_event_loop()

    elt = ELT(dsn=dsn, schema=config.elt.schema, logger=logger)
    consumer = Consumer(
        loop, elt, config.consumer.kafka.cafile,
        config.consumer.kafka.certfile, config.consumer.kafka.keyfile,
        kafka_password, config.consumer.kafka.bootstrap_servers,
        config.consumer.kafka.topic, config.consumer.consumer_group,
        config.consumer.timeout_ms, logger=logger)
    persister = Persister(loop, elt=elt, consumer=consumer, logger=logger)

    async def shotdown_task():
        persister.stop()
        await consumer.stop()
        await elt.close()

    def shotdown():
        logger.info('Shotdown hwmonitoring persister ...')
        loop.create_task(shotdown_task())

        time.sleep(2)

        logger.info('Stoping event loop ...')
        loop.stop()
        logger.info('Shutdown complete!')

    loop.add_signal_handler(signal.SIGTERM, shotdown)
    loop.add_signal_handler(signal.SIGINT, shotdown)

    try:
        loop.run_until_complete(persister.start())
    except KeyboardInterrupt:
        shotdown()


if __name__ == "__main__":
    main()
