CREATE SCHEMA IF NOT EXISTS hwmonitoring;

CREATE TABLE IF NOT EXISTS hwmonitoring.launch (
  launch_id SERIAL PRIMARY KEY,
  start_ts TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  end_ts TIMESTAMP WITHOUT TIME ZONE NULL DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS hwmonitoring.main_metrics (
  main_metrics_id BIGSERIAL PRIMARY KEY,
  launch_id INT NOT NULL,
  ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  url VARCHAR(128) NOT NULL,
  code SMALLINT NOT NULL,
  latency DECIMAL(6, 3) NOT NULL
);

CREATE INDEX ON hwmonitoring.main_metrics (launch_id, ts, url);

CREATE TABLE IF NOT EXISTS hwmonitoring.match_metrics (
  match_metrics_id BIGSERIAL PRIMARY KEY,
  launch_id INT NOT NULL,
  ts TIMESTAMP WITHOUT TIME ZONE NOT NULL,
  main_metrics_id BIGSERIAL NOT NULL,
  url VARCHAR(128) NOT NULL,
  code SMALLINT NOT NULL,
  pattern VARCHAR(128) NOT NULL,
  "count" INT NOT NULL
);

CREATE OR REPLACE FUNCTION hwmonitoring.load_metrics_from_buffer_v1(
  i_buffer_table_name REGCLASS
) RETURNS VOID AS
  $BODY$
    BEGIN
      EXECUTE FORMAT(
        'INSERT INTO hwmonitoring.main_metrics (launch_id, ts, url, code,
                                                latency)
        SELECT launch_id, TO_TIMESTAMP(ts), url, code, latency FROM %s',
        i_buffer_table_name);
      EXECUTE FORMAT(
        'INSERT INTO hwmonitoring.match_metrics (launch_id, ts,
                                                 main_metrics_id, url, code,
                                                 pattern, "count")
        SELECT bt.launch_id, bt.ts, mm.main_metrics_id, bt.url, bt.code,
               bt.pattern, bt."count"::INT
        FROM (
          SELECT launch_id, ts, url, code, "match" ->> ''pattern'' AS pattern,
                 COALESCE(("match" ->> ''count'')::INT, 0) AS "count"
          FROM (
            SELECT launch_id, TO_TIMESTAMP(ts) AS ts, url, code,
                   JSONB_ARRAY_ELEMENTS(matches) AS "match"
            FROM %s
          ) bt_row
          WHERE "match" -> ''pattern'' IS NOT NULL
        ) bt
        LEFT JOIN hwmonitoring.main_metrics mm USING (launch_id, ts, url)',
        i_buffer_table_name);
    END;
  $BODY$ LANGUAGE 'plpgsql';

CREATE TABLE IF NOT EXISTS hwmonitoring.kafka_partition_offset (
  "patition" SMALLINT PRIMARY KEY,
  "offset" BIGINT NOT NULL
);

