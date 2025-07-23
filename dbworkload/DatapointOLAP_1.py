import datetime as dt
import psycopg
import random
import time
import uuid
import polars as pl


class Datapointolap_1:
    def __init__(self, args: dict):
        # args is a dict of string passed with the --args flag
        # user passed a yaml/json, in python that's a dict object
        None



    # the setup() function is executed only once
    # when a new executing thread is started.
    # Also, the function is a vector to receive the excuting threads's unique id and the total thread count
    def setup(self, conn: psycopg.Connection, id: int, total_thread_count: int):
        with conn.cursor() as cur:
            print(
                f"My thread ID is {id}. The total count of threads is {total_thread_count}"
            )
            print(cur.execute(f"select version()").fetchone()[0])

    # the run() function returns a list of functions
    # that dbworkload will execute, sequentially.
    # Once every func has been executed, run() is re-evaluated.
    # This process continues until dbworkload exits.
    def loop(self):
        return [
                self.sql_full_polars,
                self.sql_full_polars,
                self.sql_full_polars,
                self.sql_full_polars
                # self.sql_full_polars_1
            ]


    def sql_full_dump(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    d.at, s.id, s.region,
                    d.param0, d.param1, d.param2, d.param3, d.param4
                FROM stations as s JOIN datapoints as d
                ON s.id=d.station
                AS OF SYSTEM TIME follower_read_timestamp()
                ORDER BY d.at
                """
            )
            # result = cur.fetchmany(100000)
            # while result is not None:
            #     print(len(result))
            #     cur.fetchmany(1000)
            

    def sql_full_dump_batched(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            time_freeze = None

            cur.execute(
                """
                SELECT follower_read_timestamp()
                """
            )
            (time_freeze,) = cur.fetchone()
            print("Time Freeze: ", time_freeze)

            offset = 0
            batch_szie = 1000000
            for i in range(10):

                sql = f"""
                    SELECT
                        d.at, s.id, s.region,
                        d.param0, d.param1, d.param2, d.param3, d.param4
                    FROM stations as s JOIN datapoints as d
                    ON s.id=d.station
                    AS OF SYSTEM TIME '{time_freeze}'
                    LIMIT {batch_szie} OFFSET {offset}
                """
                print(sql)

                cur.execute(sql)
                result = cur.fetchall()
                print(len(result))

                offset += batch_szie


    def sql_full_polars(self, conn: psycopg.Connection):
        query = f"""
            SELECT
                d.at, s.id, s.region,
                d.param0, d.param1, d.param2, d.param3, d.param4
            FROM stations as s JOIN datapoints as d
            ON s.id=d.station
            AS OF SYSTEM TIME follower_read_timestamp()
        """

        result = pl.read_database(
            query = query,
            connection = conn,
            iter_batches = True,
            batch_size = 10000
        )
        # print(next(result))
        # print(next(result))
        # print(next(result))


    def sql_full_polars_1(self, conn: psycopg.Connection):
        query = f"""
            SELECT * FROM fulldump ORDER BY at, id
        """

        result = pl.read_database(
            query = query,
            connection = conn,
            iter_batches = True,
            batch_size = 10000
        )


