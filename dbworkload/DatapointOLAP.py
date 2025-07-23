import datetime as dt
import psycopg
import random
import time
import uuid


class Datapointolap:
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
                # self.sql_full_dump,
                self.sql_stations_by_region,
                self.sql_datapoints_by_region,
                self.sql_datapoints_today_by_hour,
                self.sql_datapoints_yesterday_by_hour
            ]


    def sql_stations_by_region(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT region, COUNT(*) AS s_count FROM stations
                AS OF SYSTEM TIME follower_read_timestamp()
                GROUP BY region ORDER BY region
                """
            )
            cur.fetchone()



    def sql_datapoints_by_region(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.region, count(dp.at), min(dp.at), max(dp.at), sum(dp.param0),
                round(avg(dp.param2),5)
                FROM datapoints AS dp JOIN stations AS s ON s.id=dp.station
                AS OF SYSTEM TIME follower_read_timestamp()
                GROUP BY s.region ORDER BY s.region
                """
            )
            cur.fetchone()



    def sql_datapoints_today_by_hour(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH t AS (
                    SELECT generate_series  (
                        (SELECT date(now()))::timestamp,
                        (SELECT date(now()))::timestamp + '1 day' - '1 hour',
                        '1 hour'::interval
                    ) :: timestamp AS period
                )
                SELECT t.period, count(dp.at)
                FROM t AS t LEFT JOIN datapoints AS dp
                ON t.period <= dp.at AND dp.at < t.period +'1 hour'
                AS OF SYSTEM TIME follower_read_timestamp()
                GROUP BY t.period ORDER BY t.period
                """
            )
            cur.fetchone()


    def sql_datapoints_yesterday_by_hour(self, conn: psycopg.Connection):
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH t AS (
                    SELECT generate_series  (
                        (SELECT date(now()))::timestamp - INTERVAL '1 day',
                        (SELECT date(now()))::timestamp - '1 hour',
                        '1 hour'::interval
                    ) :: timestamp AS period
                )
                SELECT t.period, count(dp.at)
                FROM t AS t LEFT JOIN datapoints AS dp
                ON t.period <= dp.at AND dp.at < t.period +'1 hour'
                AS OF SYSTEM TIME follower_read_timestamp()
                GROUP BY t.period ORDER BY t.period
                """
            )
            cur.fetchone()


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
            cur.fetchone()

