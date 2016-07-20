import contextlib
import urllib.parse
import psycopg2.pool  # http://initd.org/psycopg/docs/pool.html


MIN_CONN = 1
MAX_CONN = 10

pool = None


def initialize_connection_pool(dsn):
    global pool

    url = urllib.parse.urlparse(dsn)
    pool = psycopg2.pool.ThreadedConnectionPool(
        MIN_CONN, MAX_CONN,
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )


initialize = initialize_connection_pool


@contextlib.contextmanager
def connection():
    global pool
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)


@contextlib.contextmanager
def cursor(**kwargs):
    with connection() as conn:
        cur = conn.cursor(**kwargs)
        try:
            yield cur
        finally:
            cur.close()
