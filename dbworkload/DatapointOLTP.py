import datetime as dt
import psycopg
import random
import time
import uuid
from datetime import datetime, timedelta
import string
import json


class Datapointoltp:

    def __init__(self, args: dict):
        # args is a dict of string passed with the --args flag
        # user passed a yaml/json, in python that's a dict object
        self.init_random_ranges = {
            "interval": {
                "low": 0,
                "high": 60
            },
            "date": {
                "low": datetime(2024,1,1),
                "high": datetime(2024,12,31)
            },
            "param0": {
                "low": 0,
                "high": 1000
            },
            "param1": {
                "low": -1000,
                "high": 1000
            },
            "param2": {
                "low": -1000,
                "high": 1000,
                "precision": 3
            },
            "param3": {
                "low": -1000,
                "high": 1000,
                "precision": 2
            },
            "param4": {
                "low": 8,
                "high": 32
            }
        }


    def random_date(self, d1, d2):
        retval = None
        date_range = d2 - d1
        retval = d1 + timedelta(
                                    days = random.randint(0, date_range.days),
                                    hours = random.randint(0, 24),
                                    minutes = random.randint(0, 60),
                                    seconds = random.uniform(0, 60)
                                )
        return retval.strftime("%Y-%m-%d %H:%M:%S.%f")




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
                self.sql_insert_datapoint
            ]


    def sql_insert_datapoint(self, conn: psycopg.Connection):
        datapoint = None

        with conn.transaction() as tx:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM stations ORDER BY random() LIMIT 1"
                )
                (station_id, station_region) = cur.fetchone()

                # print(station_id)

                datapoint = {
                    "interval": random.randint(
                                    self.init_random_ranges['interval']['low'],
                                    self.init_random_ranges['interval']['high']
                                ),
                    "station":  str(station_id),
                    # "date":     str(datetime.now()),
                    "date":     self.random_date(
                                    self.init_random_ranges['date']['low'],
                                    self.init_random_ranges['date']['high']
                                ),
                    "param0":   random.randint(
                                    self.init_random_ranges['param0']['low'],
                                    self.init_random_ranges['param0']['high']
                                ),
                    "param1":   random.randint(
                                    self.init_random_ranges['param1']['low'],
                                    self.init_random_ranges['param1']['high']
                                ),
                    "param2":   round(random.uniform(
                                    self.init_random_ranges['param2']['low'],
                                    self.init_random_ranges['param2']['high']
                                ), self.init_random_ranges['param2']['precision']),
                    "param3":   round(random.uniform(
                                    self.init_random_ranges['param3']['low'],
                                    self.init_random_ranges['param3']['high']
                                ), self.init_random_ranges['param3']['precision']),
                    "param4":   ''.join(random.choices(
                                    string.ascii_uppercase + string.digits,
                                    k = random.randint(
                                        self.init_random_ranges['param4']['low'],
                                        self.init_random_ranges['param4']['high']
                                    )))
                }


            with conn.cursor() as cur:
                sql = f"""
                    UPSERT INTO datapoints
                        (station, at, param0, param1, param2, param3, param4)
                        VALUES (
                            '{datapoint["station"]}', '{datapoint['date']}',
                            {datapoint['param0']}, {datapoint['param1']}, {datapoint['param2']},
                            {datapoint['param3']}, '{datapoint["param4"]}'
                        )
                """
                # print(sql)
                cur.execute(sql)



