hwmonitoring
============

This is an aiven homework task: tool for monitoring

Instalation:
------------

1. Install packages
  ```
    python setup.py install
  ```

2. Setup DB schema:
  ```
    psql `echo $DSN` -f sql/init.sql
  ```

Usage:
------

### Start the persister:

```
  DSN=postgres://postgres:mysecretpassword@localhost:5432/postgres \
  KAFKA_CERT_PASSWORD=myawesomepassword \
  hwhw-monitoring-persister --config config/persister.yaml
```

See the example of config at [config/persister.example.yaml](https://www.github.com/GSokol/whmonitoring/blob/master/config/persister.example.yaml)

### Start the scraper:

```
  KAFKA_CERT_PASSWORD=myawesomepassword \
  hw-monitoring-scraper --config config/scraper.yaml
```

See the example of config at [config/scraper.example.yaml](https://www.github.com/GSokol/whmonitoring/blob/master/config/scraper.example.yaml)
