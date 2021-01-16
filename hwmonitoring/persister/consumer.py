from asyncio import AbstractEventLoop
from logging import Logger
from typing import List

from aiokafka import (
    AIOKafkaConsumer,
    ConsumerRebalanceListener,
    TopicPartition,
)
from aiokafka.helpers import create_ssl_context

from .elt import ELT


class Consumer:
    """ Wrapper around kfka consumer """

    _consumer = None

    def __init__(
        self,
        loop: AbstractEventLoop,
        elt: ELT,
        cafile: str,
        certfile: str,
        keyfile: str,
        password: str,
        bootstrap_servers: str,
        topic: str,
        consumer_group: str,
        timeout_ms: int,
        logger: Logger,
    ) -> None:
        self._loop = loop
        self._elt = elt
        self._cafile = cafile
        self._certfile = certfile
        self._keyfile = keyfile
        self._password = password
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._consumer_group = consumer_group
        self._timeout_ms = timeout_ms
        self._logger = logger

    async def start(self) -> 'Promise[None]':
        """ Starts the consumer """

        if self._consumer is None:
            self._consumer = AIOKafkaConsumer(
                loop=self._loop,
                bootstrap_servers=self._bootstrap_servers,
                group_id=self._consumer_group,
                security_protocol='SSL',
                ssl_context=create_ssl_context(
                    cafile=self._cafile,
                    certfile=self._certfile,
                    keyfile=self._keyfile,
                    password=self._password))
            await self._consumer.start()
        self._consumer.subscribe(
            (self._topic,),
            listener=SaveOffsetsOnRebalance(self._elt, self._consumer))

    async def stop(self) -> None:
        """ Gracefuly stop the consumer """

        if self._consumer:
            await self._consumer.unsubscribe()
            await self._consumer.stop()

    async def fetch_batch(self) -> 'Promise[Iterable[bytes]]':
        """ Fetches the next batch """

        batch = await self._consumer.getmany(timeout_ms=self._timeout_ms)
        for _, messages in batch.items():
            return [msg.value for msg in messages]

    async def commit(self) -> None:
        """ Commit batch """

        await self._consumer.commit()


class SaveOffsetsOnRebalance(ConsumerRebalanceListener):
    """ Preventing rewrites, see [Kafka doc](https://kafka.apache.org/24/javadoc/index.html?org/apache/kafka/clients/consumer/ConsumerRebalanceListener.html)"""

    def __init__(self, elt: ELT, consumer: AIOKafkaConsumer) -> None:
        self._elt = elt
        self._consumer = consumer

    async def on_partitions_revoked(self,
                                    revoked: List[TopicPartition]) -> None:
        """ """

        for partition in revoked:
            await self._elt.save_kafka_partition_offset(
                partition.partition, await self._consumer.position(partition))

    async def on_partitions_assigned(self,
                                     assigned: List[TopicPartition]) -> None:
        """ """

        for partition in assigned:
            self._consumer.seek(
                partition,
                await self._elt.load_kafka_partition_offset(
                    partition.partition))
