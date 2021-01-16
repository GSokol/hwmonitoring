import json
from logging import Logger
import time
from typing import Iterable

from asyncpg import connect, PostgresError


class ELT:
    """ """

    _conn = None

    def __init__(self, dsn: str, schema: str, logger: Logger) -> None:
        self._dsn = dsn
        self._schema = schema
        self._logger = logger

    async def process_batch(self, batch: Iterable[bytes]) -> 'Promise[bool]':
        """ Process batch from kafka
            Only hwmonitoring.model.ModelV1 support """

        if batch is None:
            return

        await self._ensure_conn()
        try:
            # Gether new launch id
            new_launch_id = (await self._conn.fetchrow(
                '''INSERT INTO "%s".launch (end_ts) VALUES (DEFAULT)
                 RETURNING launch_id''' % (self._schema,),
            ))['launch_id']

            buffer_table_name = 'load_buffer_%d' % (new_launch_id,)

            # Create tmp table buffer
            await self._conn.execute('''
                CREATE TEMPORARY TABLE "%s" (
                    id SERIAL PRIMARY KEY,
                    launch_id INT NOT NULL DEFAULT %d,
                    ts DOUBLE PRECISION NOT NULL,
                    url VARCHAR(128) NOT NULL,
                    code SMALLINT NOT NULL,
                    latency DECIMAL(6, 3) NOT NULL,
                    matches JSONB NOT NULL
                )
            ''' % (buffer_table_name, new_launch_id,))

            # Records generator
            rows = map(
                lambda model: (
                    model['timestamp'], model['url'], model['code'],
                    model['latency'],
                    json.dumps(model['matches']),),
                [json.loads(msg.decode('utf-8')) for msg in batch])
            # Load data
            await self._conn.copy_records_to_table(
                buffer_table_name,
                columns=['ts', 'url', 'code', 'latency', 'matches',],
                records=rows)

            # Run tranform
            await self._conn.fetch(
                'SELECT "%s".load_metrics_from_buffer_v1($1)' % (
                    self._schema,), buffer_table_name)

            await self._conn.execute(
                '''UPDATE "%s".launch
                SET end_ts = TO_TIMESTAMP($2)
                WHERE launch_id = $1''' % (self._schema,),
                new_launch_id, int(time.time()))
            await self._conn.execute(
                'DROP TABLE "%s"' % (buffer_table_name,))

            return True
        except PostgresError as err:
            self._logger.error('Failed to load batch: %s', str(err))
            return False

    async def save_kafka_partition_offset(self, partition: int,
                                          offset: int) -> None:
        """ Save kafka's partition offset """

        await self._ensure_conn()
        await self._conn.execute('''
            INSERT INTO "%s".kafka_partition_offset ("patition", "offset")
                VALUES ($1, $2) ON CONFLICT ("patition") DO UPDATE
                SET "offset" = $2 WHERE "patition" = $1''' % (self._schema,),
                                 partition, offset)

    async def load_kafka_partition_offset(self,
                                          partition: int) -> 'Promise[int]':
        """ Load kafka's partition offset """

        await self._ensure_conn()
        row = await self._conn.fetchrow('''SELECT "offset" FROM
            "%s".kafka_partition_offset WHERE "patition" = $1''' % (
            self._schema,),
            partition)
        if row is None:
            return 0
        return row['offset']

    async def close(self) -> 'Promise[None]':
        """ Graceful close PG connextion """

        if self._conn is not None:
            await self._conn.close()

    async def _ensure_conn(self) -> None:
        """ make sure the connection is opened """

        if self._conn is None:
            self._conn = await connect(self._dsn)
